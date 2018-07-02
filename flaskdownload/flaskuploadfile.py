from flask import Flask, send_from_directory, make_response
import gevent.monkey
from pathlib import Path
from gevent.pywsgi import WSGIServer
gevent.monkey.patch_all()
app = Flask(__name__)


@app.route('/api/download', methods=['GET'])
def download():
    filepath = Path('D:\gitcode/shensiwork/flaskdownload/')
    filename = 'test.txt'
    # 中文
    response = make_response(send_from_directory(directory=filepath, filename=filename, as_attachment=True))
    response.headers["Content-Disposition"] = "attachment; filename={}".format(filename.encode().decode('latin-1'))
    return response


if __name__ == '__main__':
    http_server = WSGIServer(('0.0.0.0', 8014), app)
    try:
        print("Start at " + http_server.server_host +
              ':' + str(http_server.server_port))
        http_server.serve_forever()
    except(KeyboardInterrupt):
        print('Exit...')