"""
邮箱的APP接口
create by swm
2018/06/07
"""

from flask import Flask, request, Response
import json
import gevent.monkey
from gevent.pywsgi import WSGIServer
gevent.monkey.patch_all()
# 内部引用
from .tom.tomspider import MAIL
app = Flask(__name__)


@app.route('/mail/tom/cookielogin', methods=['post'])
def cookieloginapi():
    args = json.loads(request.data)
    cookies = args['cookies']
    res = MAIL().cookielogin(cookies)
    if res:
        info = {
            'status': True,
            'cookies': res
        }
    else:
        info = {
            'status': False
        }
    return Response(json.dumps(info), mimetype="application/json")


@app.route('/mail/tom/accountlogin', methods=['post'])
def accountlogin():
    args = json.loads(request.data)
    account = args['account']
    pwd = args['password']
    res = MAIL().accountlogin(account, pwd)
    if res:
        info = {
            'status': True,
            'cookies': res
        }
    else:
        info = {
            'status': False
        }
    return Response(json.dumps(info), mimetype="application/json")


@app.route('/mail/tom/geteml', methods=['post'])
def geteml():
    args = json.loads(request.data)
    cookies = args['cookies']
    res = MAIL().getthemail(cookies)
    if res:
        info = {
            'status': True,
            'cookies': res
        }
    else:
        info = {
            'status': False
        }
    return Response(json.dumps(info), mimetype="application/json")


@app.route('/mail/tom/getcontacts', methods=['post'])
def getcontacts():
    args = json.loads(request.data)
    cookies = args['cookies']
    res = MAIL().getcontacts(cookies)
    if res:
        info = {
            'status': True,
            'cookies': res
        }
    else:
        info = {
            'status': False
        }
    return Response(json.dumps(info), mimetype="application/json")


if __name__ == '__main__':
    http_server = WSGIServer(('0.0.0.0', 8000), app)
    try:
        print("Start at " + http_server.server_host +
              ':' + str(http_server.server_port))
        http_server.serve_forever()
    except KeyboardInterrupt as err:
        print(err)