"""
twitter flask API
create by swm
2018/06/13
"""
from flask import Flask, request, Response
import json
import gevent.monkey
from gevent.pywsgi import WSGIServer
gevent.monkey.patch_all()
# 内部引用
from tweetspider import TWEET
app = Flask(__name__)


@app.route('/twitter/search', methods=['post'])
def cookieloginapi():
    args = json.loads(request.data)
    key = args['searchkey']
    res = TWEET(key).startapp()
    if res:
        info = {
            'status': True,
            'info': 'collect complete.'
        }
    else:
        info = {
            'status': False,
            'info': 'There is something wrong when collecting.'
        }
    return Response(json.dumps(info), mimetype="application/json")


if __name__ == '__main__':
    http_server = WSGIServer(('0.0.0.0', 8001), app)
    try:
        print("Start at " + http_server.server_host +
              ':' + str(http_server.server_port))
        http_server.serve_forever()
    except KeyboardInterrupt as err:
        print(err)