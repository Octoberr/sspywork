"""
下载链接
create by swm
20180709
"""
from pathlib import Path
import requests

class DN:

    def __init__(self, url, name):
        self.url = url
        self.name = name
        self.path = Path('img')
        self.usragent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
        self.headers = {
            'User-Agent': self.usragent
        }

    def getdata(self):
        res = requests.get(self.url, headers=self.headers)
        fp = open(self.path/name, 'wb')
        fp.write(res.content)
        fp.close()
        print('done')


if __name__ == '__main__':
    url = 'https://pic2.zhimg.com/v2-a546643e9e4457d30089073d89a26f59_b.gif'
    name = 'test.gif'
    dn = DN(url, name)
    dn.getdata()
