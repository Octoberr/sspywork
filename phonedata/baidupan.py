"""
获取百度盘的信息
createby swm
2018/05/29
"""

import requests
import json

class MAIL:

    def __init__(self):
        self.cookie = 'BAIDUID=198DC60C9B6E7A8C255B6248FDDAFAC4:FG=1; H_WISE_SIDS=110314_100808_123408_123486_120170_118895_118865_118846_118821_118789_120549_107320_117333_117436_122791_123572_122959_123812_121143_123700_119326_110085_123289; PSINO=6; SE_LAUNCH=5%3A25458335; BDORZ=AE84CDB3A529C0F8A2B9DCDD1D18B695; pgv_pvi=4719155200; pgv_si=s5705408512; PANWEB=1; FP_UID=06c2fdd2a436c552a1e87b0de91d3b07; BDUSS=Q1VFMyZUFQem1OY0hkbW9sMENQN2NoNmdJQXlmLUlZcHZDbkNlbUFwbWVwalJiQVFBQUFBJCQAAAAAAAAAAAEAAABHbA1zv8mwrrXEMG8wbzBvMDEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAJ4ZDVueGQ1bY2; Hm_lvt_7a3960b6f067eb0085b7f96ff5e660b0=1527585187; cflag=15%3A3; PMS_JT=%28%7B%22s%22%3A1527585726702%2C%22r%22%3A%22https%3A//pan.baidu.com/disk/home%3Fadapt%3Dpc%26fr%3Dftw%22%7D%29; Hm_lpvt_7a3960b6f067eb0085b7f96ff5e660b0=1527585732; PANPSC=12776925009509367471%3AWaz2A%2F7j1vUazJEavtchZ%2Bn90oj%2BY%2FIsmx0Okynvri548YWvwM7hnvqstS0LQVXoZL8jhHrk0tp4F6H61hEiONCBzEj9IkR4%2Fx0mUYYevj2tUq%2FdzxBw4g7%2BrBdpKzwe0ocSij%2FG6mUnih65clERtryHDAnhPhMz5dNt%2BsRbU69UMSLhYBPCxc5TMpqnKCFM'
        self.usragent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
        self.headers ={
            'Cookie': self.cookie,
            'User-Agent': self.usragent
        }

    def getdirlist(self):
        # 获取文件列表
        url = 'https://pan.baidu.com/api/list?dir=%2F&bdstoken=f2a107be534b8e0205605427d6649599&logid=MTUyNzU4NTczNzcxOTAuOTE2Nzc5NTg0MDA4NTUyMg==&num=100&order=time&desc=1&clienttype=0&showempty=0&web=1&page=1&channel=chunlei&web=1&app_id=250528'
        res = requests.get(url, headers=self.headers)
        resdic = json.loads(res.text)

        print(resdic['list'])

    def getdirname(self):
        # 获取文件名字
        url = 'https://pan.baidu.com/api/list?order=time&desc=1&showempty=0&web=1&page=1&num=100&dir=%2Fapps%2Fbaidu_shurufa&t=0.677987124977468&channel=chunlei&web=1&app_id=250528&bdstoken=f2a107be534b8e0205605427d6649599&logid=MTUyNzU4NjY3Mjg3NjAuNzI4MzY1OTM4MjE5MTg2Nw==&clienttype=0&startLogTime=1527586672876'
        res = requests.get(url, headers=self.headers)
        resdict = json.loads(res.text)
        for el in resdict:
            print(el)
        # print(resdict)

if __name__ == '__main__':
    MAIL().getdirlist()