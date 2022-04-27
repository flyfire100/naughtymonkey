from mitmproxy import ctx
from mitmproxy.http import *
import requests
import json


class Monkey():
    def response(self, flow):
        headers = {}
        for key, value in flow.request.headers.items():
            headers[key] = value
        response_headers = {}
        for key, value in flow.response.headers.items():
            response_headers[key] = value

        data = {
            "url": str(flow.request.url),
            "headers": headers,
            "content": json.loads(flow.request.get_text()),
            "response_code": flow.response.status_code,
            "response_headers": response_headers,
            "response_body": json.loads(flow.response.get_text())
        }
        #ctx.log.info( data )
        try:
            r = requests.post("http://127.0.0.1:18674/naughtymonkey", json=data)
            if r.status_code == 404:
                pass
            else:
                ctx.log.info(  "==================="  )
                flow.response.status_code = r.status_code
                ctx.log.info( r.text )
                flow.response.set_text( r.text  )
                ctx.log.info( flow.response   )
        except Exception as e:
            ctx.log.info(str(e))


addons = [
    Monkey()
]
