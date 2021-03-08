import re
from .spidersocialbase import SpiderSocialBase
from datetime import datetime
import pytz
import requests
import uuid
import execjs
from commonbaby.helpers import helper_crypto
from commonbaby.helpers.helper_str import substring
import time
import traceback
from datacontract.ecommandstatus import ECommandStatus
from datacontract.idowndataset import EBackResult


class SpiderBaiduTieba(SpiderSocialBase):

    def __init__(self, task, appcfg, clientid):
        super(SpiderBaiduTieba, self).__init__(task, appcfg, clientid)

    def _check_registration(self):
        """
        查询手机号是否注册了百度贴吧
        :param account:
        :return:
        """
        t = time.strftime('%Y-%m-%d %H:%M:%S')
        ti = int(datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() * 1000)
        try:
            html = self._ha.getstring('https://passport.baidu.com/v2/?reg&tpl=tb&u=//tieba.baidu.com', headers="""
Host: passport.baidu.com
Connection: keep-alive
Pragma: no-cache
Cache-Control: no-cache
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
""", encoding='utf-8')
            html.encoding = 'utf-8'
            # print(html.text)
            gid = 'DD9D1FD-752B-4AC4-9BE0-CB699316505D'
            gid = str(uuid.uuid1()).upper()[1:]
            gid = gid[:13] + '4' + gid[14:]
            js = """
            getUniqueId = function(e) {
                return e + Math.floor(2147483648 * Math.random()).toString(36)
            }"""
            ctx = execjs.compile(js)
            callback = ctx.call('getUniqueId', 'bd__cbs__')
            html = self._ha.getstring(
                f'https://passport.baidu.com/v2/api/?getapi&tpl=tb&apiver=v3&tt={ti}&class=regPhone&gid={gid}&app=&traceid=&callback={callback}',
                headers="""
Host: passport.baidu.com
Connection: keep-alive
Pragma: no-cache
Cache-Control: no-cache
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
Accept: */*
Referer: https://passport.baidu.com/v2/?reg&tpl=tb&u=//tieba.baidu.com
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
""")
            token = substring(html, '"token" : "', '"')
            #
            # js = """
            # function hex_md5(s) {
            #     return binl2hex(core_md5(str2binl(s), s.length * chrsz))
            # }
            # function get_moonshad(phone) {
            #     n = hex_md5(phone + "Moonshadow");
            #     n = n.replace(/o/, "ow").replace(/d/, "do").replace(/a/, "ad"),
            #     n = n.replace(/h/, "ha").replace(/s/, "sh").replace(/n/, "ns").replace(/m/, "mo"),
            #     return n
            # }
            # """
            # moon = execjs.compile(js)
            # moonshad = moon.call('get_moonshad', self.task.phone)
            moonshad = helper_crypto.get_md5_from_str(self.task.phone + "Moonshadow")
            moonshad = re.sub(r'o', 'o~', moonshad, 1)
            moonshad = re.sub(r'd', 'd!', moonshad, 1)
            moonshad = re.sub(r'a', 'a@', moonshad, 1)
            moonshad = re.sub(r'h', 'h#', moonshad, 1)
            moonshad = re.sub(r's', 's$', moonshad, 1)
            moonshad = re.sub(r'n', 'n%', moonshad, 1)
            moonshad = re.sub(r'm', 'm^', moonshad, 1)
            moonshad = moonshad.replace('~', 'w').replace('!', 'o').replace('@', 'd').replace('#', 'a').replace('$',
                                                                                                                'h').replace(
                '%', 's').replace('^', 'n')
            callback = ctx.call('getUniqueId', 'bd__cbs__')
            url = f"https://passport.baidu.com/v2/?regphonecheck&token={token}&tpl=tb&apiver=v3&tt={ti}&phone={self.task.phone}&moonshad={moonshad}&countrycode=&gid={gid}&exchange=0&isexchangeable=1&action=reg&traceid=&callback={callback}"
            headers = """
Host: passport.baidu.com
Connection: keep-alive
Pragma: no-cache
Cache-Control: no-cache
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
Accept: */*
Referer: https://passport.baidu.com/v2/?reg&tpl=tb&u=//tieba.baidu.com
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
"""
            response = self._ha.get_response(url, headers=headers)
            response.encoding = 'utf-8'
            # print(response.text)
            if '"400001"' in response.text:
                self._write_task_back(ECommandStatus.Succeed, 'Registered', t, EBackResult.Registerd)
            else:
                self._write_task_back(ECommandStatus.Succeed, 'Not Registered', t, EBackResult.UnRegisterd)
        except Exception:
            self._logger.error('Uber check registration fail: {}'.format(traceback.format_exc()))
            self._write_task_back(ECommandStatus.Failed, 'Check registration fail', t, EBackResult.CheckRegisterdFail)
        return
