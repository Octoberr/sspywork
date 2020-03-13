#coding: utf-8
from enum import Enum
import datetime
import requests
import random

class Level(Enum):
    info = 0
    debug = 1
    error = 2
    warming = 3
    success = 4

level_string = ['[Info]', '[Debug]', '[Error]', '[Warming]', '[Success]']
    
class Exploit():
    def __init__(self, url, taskid=0, targetid=0, cmd_connect='', data_redirect='', dns_server='', proxies={}):
        self.url = url
        self.taskid = taskid
        self.targetid = targetid
        self.cmd_connect = cmd_connect
        self.data_redirect = data_redirect
        self.dns_server = dns_server
        self.proxies = proxies
        self.log_data = []
        self.shell_data = []
        
    def meta_info(self):
        self.report('meta_info not implement', Level.error)
        
    def exploit(self):
        self.report('exploit not implement', Level.error)
    
    def report(self, message, level=Level.info):
        global level_string
        message_time = datetime.datetime.now()
        _level = level.value if type(level) is Level else level
        message_line = '%s %-9s %s' %(message_time.strftime('%Y-%m-%d %H:%M:%S'), level_string[_level], message)
        try:
            print message_line.decode('utf8').encode('gbk')
        except:
            print message_line
        data = {
            'taskid': self.taskid,
            'targetid': self.targetid,
            'level': _level,
            'message': message,
            'create_time': self.datetime_fmt()
        }
        self.log_data.append(data)
        return 

    def shell_info(self, shell_path, shell_password, shell_type):
        try:
            req = session()
            rsp = req.post(url=shell_path, data={shell_password:"print '5a09880adca1f5c24c2b755f41982b5'.chr(97);"})
            if '5a09880adca1f5c24c2b755f41982b5a' in rsp.text:
                self.report('shell:%s, password:%s, type:%s' % (shell_path, shell_password, shell_type), Level.success)
                data = {
                    'taskid': self.taskid,
                    'targetid': self.targetid,
                    'shell_path': shell_path,
                    'shell_password': shell_password,
                    'cmd_connect': self.cmd_connect,
                    'create_time': self.datetime_fmt()
                }
                self.shell_data.append(data)
                return
        except Exception as e:
            pass
        return None
        
    def datetime_fmt(self):
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        
        
import requests
# 禁用安全请求警告
# from requests.packages.urllib3.exceptions import InsecureRequestWarning
# requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class session(requests.Session):
    def __init__(self, *args, **kwargs):
        self.conf = {
            'timeout': 3,
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36',
            },
            'proxies':{
            },
            'verify': False,
        }
        self.conf.update(kwargs)
        super(session, self).__init__()
     
    def get(self, *args, **kwargs):
        temp = dict(**self.conf)
        temp.update(kwargs)
        if len(args) == 1:
            temp.update({'url':args[0]})
        return super(session, self).get(**temp)
        
    def post(self, *args, **kwargs):
        temp = dict(**self.conf)
        temp.update(kwargs)
        if len(args) == 1:
            temp.update({'url':args[0]})
        return super(session, self).post(**temp)
        
        
def get_random_password(pass_len=8):
    string = '1234567888990abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ' * 3
    s = list(string)
    random.shuffle(s)
    return ''.join(s[:pass_len])
    
        