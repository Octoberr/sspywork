from pathlib import Path

import http.client, mimetypes, urllib, json, time, requests
from retrying import retry


######################################################################

class YDMHttp:
    apiurl = 'http://api.yundama.com/api.php'
    username = ''
    password = ''
    appid = ''
    appkey = ''

    def __init__(self, username, password, appid, appkey):
        self.username = username
        self.password = password
        self.appid = str(appid)
        self.appkey = appkey

    def request(self, fields, files=[]):
        response = self.post_url(self.apiurl, fields, files)
        response = json.loads(response)
        return response

    def balance(self):
        data = {'method': 'balance', 'username': self.username, 'password': self.password, 'appid': self.appid,
                'appkey': self.appkey}
        response = self.request(data)
        if (response):
            if (response['ret'] and response['ret'] < 0):
                return response['ret']
            else:
                return response['balance']
        else:
            return -9001

    def login(self):
        data = {'method': 'login', 'username': self.username, 'password': self.password, 'appid': self.appid,
                'appkey': self.appkey}
        response = self.request(data)
        if (response):
            if (response['ret'] and response['ret'] < 0):
                return response['ret']
            else:
                return response['uid']
        else:
            return -9001

    def upload(self, filename, codetype, timeout):
        data = {'method': 'upload', 'username': self.username, 'password': self.password, 'appid': self.appid,
                'appkey': self.appkey, 'codetype': str(codetype), 'timeout': str(timeout)}
        file = {'file': filename}
        response = self.request(data, file)
        if (response):
            if (response['ret'] and response['ret'] < 0):
                return response['ret']
            else:
                return response['cid']
        else:
            return -9001

    def result(self, cid):
        data = {'method': 'result', 'username': self.username, 'password': self.password, 'appid': self.appid,
                'appkey': self.appkey, 'cid': str(cid)}
        response = self.request(data)
        return response and response['text'] or ''

    # 识别验证码
    def decode(self, filename, codetype, timeout):
        cid = self.upload(filename, codetype, timeout)
        if (cid > 0):
            for i in range(0, timeout):
                result = self.result(cid)
                if (result != ''):
                    return cid, result
                else:
                    time.sleep(1)
            return -3003, ''
        else:
            return cid, ''

    # 验证码报错调用验证码
    def report(self, cid):
        data = {'method': 'report', 'username': self.username, 'password': self.password, 'appid': self.appid,
                'appkey': self.appkey, 'cid': str(cid), 'flag': '0'}
        response = self.request(data)
        if (response):
            return response['ret']
        else:
            return -9001

    def post_url(self, url, fields, files=[]):
        for key in files:
            files[key] = open(files[key], 'rb')
        res = requests.post(url, files=files, data=fields)
        return res.text


class RECQUNA(object):

    def __init__(self):
        self.all_img_path = Path(r'D:\swmdata\traindata\train_original_data')
        self.ok_img = Path(r"D:\swmdata\traindata\origin")
        self.suffix = '.png'

    @retry(stop_max_attempt_number=10, wait_fixed=10000)
    def get_the_name(self):
        try:
            # 用户名
            username = 'october'

            # 密码
            password = 'swm123'

            # 软件ＩＤ，开发者分成必要参数。登录开发者后台【我的软件】获得！
            appid = 7374

            # 软件密钥，开发者分成必要参数。登录开发者后台【我的软件】获得！
            appkey = 'ed47a4f7308a325aad8b1fd2fe487710'

            # 验证码类型，# 例：1004表示4位字母数字，不同类型收费不同。请准确填写，否则影响识别率。在此查询所有类型 http://www.yundama.com/price.html
            codetype = 1004

            # 超时时间，秒
            timeout = 60

            # 初始化
            yundama = YDMHttp(username, password, appid, appkey)

            # 登陆云打码
            uid = yundama.login()
            print('uid: %s' % uid)

            # 查询余额
            balance = yundama.balance()
            print('balance: %s' % balance)
            for child in self.all_img_path.iterdir():
                filename = str(child)
                # 开始识别，图片路径，验证码类型ID，超时时间（秒），识别结果
                cid, result = yundama.decode(filename, codetype, timeout)
                print('cid: %s, result: %s' % (cid, result))
                target = self.ok_img / (result.upper() + '_' + str(time.time()).replace('.', '') + self.suffix)
                child.rename(target)
        except Exception as es:
            print(es)


if __name__ == '__main__':
    r = RECQUNA()
    r.get_the_name()
