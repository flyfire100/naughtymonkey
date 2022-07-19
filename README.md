# naughtymonkey

通过iptables进行nat,然后使用mitmproxy对码流进行拦截和篡改,达到mock服务的目的,目前支持restful接口的mock


# 架构

没有naughtymonkey时候:
服务A(1.1.1.1) -->服务B(2.2.2.2:8888) 接收请求
服务A(1.1.1.1) <--服务B(2.2.2.2:8888) 返回响应

使用naughtymonkey时候:
服务A(1.1.1.1) -->服务B网卡(iptables) --> naughtymonkey(3.3.3.3:8080) --> 服务B(2.2.2.2:8888)
服务A(1.1.1.1) <--服务B网卡(iptables) <-- naughtymonkey(3.3.3.3:8080) 此处可以篡改响应  <-- 服务B(2.2.2.2:8888)返回响应


1 在服务B上面执行monkeyagent.sh 配置iptables规则,把服务A请求的码流都透传到naughtymonkey
2 在naughtymonkey的界面配置拦截的URL地址,只有匹配到URL才会进行拦截操作
3 在naughtymonkey的界面配置拦截和篡改任务,当匹配到条件的请求过来后就按照任务中的码流进行返回


# 依赖
1 naughtymonkey依赖mongodb,所以需要部署mongodb
2 python3,同时依赖的包很多,懒的梳理了,哪个没有自己添加吧
