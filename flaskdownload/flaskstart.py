from flask import Flask
import gevent.monkey
from gevent.pywsgi import WSGIServer
gevent.monkey.patch_all()
app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello, I am your nightmire!'

if __name__ == '__main__':
    http_server = WSGIServer(('0.0.0.0', 5000), app)
    try:
        print("Start at " + http_server.server_host +
              ':' + str(http_server.server_port))
        http_server.serve_forever()
    except(KeyboardInterrupt):
        print('Exit...')