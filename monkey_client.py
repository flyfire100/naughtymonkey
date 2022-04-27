import tornado.ioloop
import tornado.web
import pymongo
import json
from functools import partial
from pywebio.platform.tornado import webio_handler
from pywebio.input import *
from pywebio.output import *
from pywebio.session import *
from ast import literal_eval
import pywebio.pin as pin
from jsonpath import jsonpath

myclient = pymongo.MongoClient("mongodb://127.0.0.1:27017/")
dblist = myclient.list_database_names()
print( "dblist is", dblist)
# 历史记录,每个集合是一个url,按照url进行缓存
mydb = myclient["record"]
monitor_urls = mydb.list_collection_names()
print( "monitor_urls is", monitor_urls )

# 任务记录,每个集合是一个url,按照url下发任务
mytaskdb = myclient["task"]
task_urls = mytaskdb.list_collection_names()
print( "task_urls is", task_urls )


# 处理monkey发送的码流,进行保存和更改
class MainHandler(tornado.web.RequestHandler):
    def post(self,*args, **kwargs):
        #print(self.request.body)
        data = json.loads( self.request.body )
        #print(data)
        monitor_urls = mydb.list_collection_names()
        for url in monitor_urls:
            if url in data["url"]:
                mydb[url].insert_one(data)
                break
        # 进行判断,返回匹配条件的内容
        task_urls = mytaskdb.list_collection_names()
        for url in task_urls:
            if url in data["url"]:
                for task in mytaskdb[url].find().sort("_id",-1).limit(100):
                    name = task.get("name")
                    condition = task.get("condition")
                    condition_list = get_task_condition( condition )
                    if condition_list == False:
                        continue
                    item_name = condition_list[0]
                    item_value = condition_list[1]
                    response = task.get("response")
                    req = data.get("content")
                    if response == None or response.replace(" ","") == "":
                        continue
                    match_result = jsonpath( req, "$.."+item_name )
                    if match_result != False:
                        for item in match_result:
                            if item_value in item:
                                print( response )
                                response = literal_eval(response)
                                self.write( json.dumps(response)  )
                                print("convert req", name, response)
                                return
        # 没有匹配到任何条件则直接返回404,不对响应进行任何处理
        self.set_status(404, reason=None)



# 校验任务中condition是否合法
def get_task_condition( condition ):
    condition_list = condition.split("==")
    if len(condition_list) != 2:
        #print( condition_list )
        return False
    return condition_list



# 通过接口设置任务详情
class SetResponse( tornado.web.RequestHandler  ):
    def post(self, *args, **kwargs ):
        print(self.request.body  )
        data = json.loads( self.request.body )
        # data: {"url":"xxxx", "condition":"$.reqid", "value":"reqidxxxxxx", "name":"xxxxx", "response":"xxxxxxxxx"}
        url = data.get("url")
        if url == None or url == "":
            self.set_status(404, reason="{'msg':'url is empty'}")
            return
        name = data[url].find_one({"name":data["name"]})
        if name == None :
            mytaskdb[url].add_one( data )
            self.write( "{'msg':'success'}" )
            return
        self.set_status(404, reason="{'msg':'name already exists'}")

    def delete( self, *args, **kwargs  ):
        print( self.request.body  )
        data = json.loads( self.request.body )
        # data: {"url":"xxx","name":"xxxxxx"}
        url = data["url"]
        if url == None or url == "":
            self.set_status(404, reason="{'msg':'url is empty'}")
            return
        mytaskdb[url].delete_one( data  )
        self.write( "{'msg':'success'}"  )


# 界面相关操作
def controler():
    set_env(title='NaughtyMonkey', output_animation=False, output_max_width='100%')
    put_row([put_button("监控URL管理", monitor_url_controler),None,
            put_button("历史码流", mitm_record_controler),None,
            put_button("拦截任务",task_controler )],size="30% 10px 30% 10px 30%")

    with use_scope("global_content",True):
        put_markdown("# 监控URL管理界面")
        monitor_url_controler()

# 清理所有的scope
def clean_all_scope():
    clear("monitor_urls")
    clear("record_list")
    clear("task_list")


# 监控的url信息
def monitor_url_controler():
    # 增加监控URL信息
    def add_monitor_url():
        url = pin.pin["url"]
        if url in mydb.list_collection_names():
            popup('添加结果', 'URL在监控信息中已经存在')
        else:
            mydb[url].insert_one( {"test":"test"} )
            mydb[url].delete_one( {'test':"test"} )
            popup('添加结果', '添加成功')
        show_monitor_urls( mydb.list_collection_names()   )

    # 删除监控URL信息
    def delete_monitor_url( url ):
        mydb[url].drop()
        popup('删除结果', '删除成功')
        show_monitor_urls( mydb.list_collection_names()  )

    # 查询监控URL信息
    def search_monitor_url():
        url = pin.pin["url"]
        result_items = []
        for item in mydb.list_collection_names():
            if url in item:
                result_items.append( item )
        show_monitor_urls( result_items  )

    # 展示监控信息
    def show_monitor_urls( items ):
        with use_scope("monitor_urls",True):
            out_put = []
            out_put.append( ["被监控的URL","操作"] )
            for item in items:
                out_put.append( [ item, put_button( "删除", partial(delete_monitor_url,item) )  ]   )
            put_table( out_put ).style("width:100%")
    # 展示结果
    with use_scope("global_content",True):
        clean_all_scope()
        put_text("请输入需要监控的url字段")
        put_row( [ pin.put_input("url",type=TEXT),None,
             put_button('添加', add_monitor_url),None,
             put_button('查询', search_monitor_url)],size='80% 10px 8% 10px 8%'    )
        show_monitor_urls( mydb.list_collection_names()  )


# 历史码流
def mitm_record_controler():
    # 展示详情
    def show_detail( url, data_id  ):
        data = mydb[url].find_one( {"_id":data_id} )
        set_env(title="详细信息",output_max_width='100%')
        popup('详情信息', [
            put_table([
                ['Type', 'Detail'],
                ['URL', data["url"] ],
                ['REQ_HEADERS', data['headers'] ],
                ['REQ_CONTENT', data['content']   ],
                ['RESPONSE_CODE', data['response_code'] ],
                ['RESPONSE_HEADERS', data['response_headers'] ],
                ['RESPONSE_BODY', data['response_body'] ]
            ])
       ],size='large')


    # 展示最近50条的记录结果
    def show_record(  ):
        url = pin.pin['url']
        condition = pin.pin['condition']
        if url.replace(" ","") == "":
            toast("请选择URL",color='error')
            return

        if condition.replace(" ","") == "":
            datas = mydb[url].find().sort("_id",-1).limit(50)
        else:
            print( condition )

            if  len( condition.split("==")  ) != 2:
                toast("查询条件输入错误,请检查格式是否正确",color='error')
                return

            item_name = condition.split("==")[0]
            item_value = condition.split("==")[1]
            datas = mydb[url].find( ).sort("_id",-1).limit(100)
            out_datas = []
            for data in datas:
                for item  in  jsonpath( data,"$.."+item_name  ):
                    if item_value in item:
                        out_datas.append( data )
                        break
            datas = out_datas
            """
            try:
                condition_dict = literal_eval( condition  )
                print( condition_dict  )
            except Exception as e:
                toast("查询条件输入错误,请检查格式是否正确",color='error')
                return
            finally:
                if not isinstance( condition_dict, dict ):
                    toast("查询条件输入错误,请检查格式是否正确",color='error')
                    return
            """
        out_put = [ ["响应","详情"]  ]
        for item in datas:
            if "content" not in item.keys():
                continue
            response_body = json.dumps( item['response_body'], indent=4, separators=(',', ':')  )
            out_item = [ item['response_body'], put_button("详情", onclick=partial(show_detail, data_id=item["_id"], url=url)) ]
            out_put.append( out_item )
        with use_scope("record_list",True):
            put_table( out_put  )


    # 展示结果
    with use_scope("global_content",True):
        clean_all_scope()
        record_urls = mydb.list_collection_names()
        put_row(
            [ pin.put_input( "url", datalist=record_urls, placeholder="选择要查询的URL"),None,
              pin.put_input( "condition",placeholder="输入查询条件" ),None,
              put_button('查询',show_record)
            ],size="60% 10px 25% 10px 5%"
        )


# 创建任务
def task_controler():
    # 添加任务
    def add_task():
        url = pin.pin["url"]
        condition = pin.pin["condition"]
        value = pin.pin["value"]
        name = pin.pin["name"]
        data = {
            "url":url,
            "condition":condition,
            "name":name
        }
        for key in data.keys():
            if data[key].replace(" ","") == "":
                toast("请填写任务条件",color='error')
                return
        result = mytaskdb[url].find_one( {"name":name}  )
        if result != None:
            toast("任务名称已经存在",color='error')
            return
        mytaskdb[url].insert_one( data  )
        show_detail()

    # 更新任务
    def update_task(url,name,response):

        def update_task_db( url, name ):
            response = pin.pin["response"]
            mytaskdb[url].update_one( {"name":name},{ "$set":{"response":response} }   )
            close_popup()
            show_detail()

        data = mytaskdb[url].find_one( {"name":name} )
        set_env(title="更新信息",output_max_width='100%')
        with popup("更新响应") as s:
             popup_scope = s
             put_button( "修改", partial( update_task_db, url = url, name=name )  )
        pin.put_textarea("response",value=data.get("response"),rows=60,scope=popup_scope, position=0  ),

        show_detail()


    # 删除任务
    def delete_task(url,name):
        mytaskdb[url].delete_one( {"name":name}  )
        show_detail()

    # 查询任务
    def query_task():
        show_detail()

    # 展示任务列表
    def show_detail():
        url = pin.pin["url"]
        condition = pin.pin["condition"]
        value = pin.pin["value"]
        name = pin.pin["name"]
        if url.replace(" ","") == "":
            toast("请选择/输入URL",color='error')
            return
        datas = mytaskdb[url].find().sort("_id",-1).limit(100)
        out_put = [ ["任务名称","匹配条件","返回响应","修改","删除"]  ]
        for item in datas:
            t_name = item.get("name")
            t_response = item.get("response")
            t_condition = item.get("condition")
            data =[
                t_name,
                t_condition,
                t_response,
                put_button("修改",partial(update_task,url=url,name=t_name,response=t_response)),
                put_button("删除",partial(delete_task,url=url,name=t_name))
            ]
            out_put.append(data)
        with use_scope("task_list",True):
            put_table( out_put )


    # 展示当前的任务
    with use_scope( "global_content",True ):
        clean_all_scope()
        task_urls = mytaskdb.list_collection_names()
        put_row(
            [ pin.put_input( "url",datalist=task_urls , placeholder="选择任务对应的URL" ),None,
              pin.put_input( "condition",placeholder="输入匹配条件" ),None,
              pin.put_input( "name",placeholder="输入任务名称" ),None,
              put_button( "添加",add_task ),None,
              put_button( "查询",query_task)
            ],size="40% 5px 30% 5px 8% 5px 8% 5px 8%")

# 主函数
if __name__ == "__main__":
    application = tornado.web.Application([
        #(r"/(.*)", MainHandler),
        (r"/naughtymonkey", MainHandler),
        (r"/tool",webio_handler(controler)),
        (r"/setresponse",SetResponse  ),
    ])
    application.listen(18674)
    tornado.ioloop.IOLoop.current().start()
