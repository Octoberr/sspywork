import hashlib
import io
import json
import re
import random
import time
import traceback
import pytz
from urllib.parse import quote_plus
from datetime import datetime

import execjs
from commonbaby.helpers.helper_str import substring
from ...clientdatafeedback import INETDISKFILE, INETDISKFILELIST
from .spiderinetdiskbase import SpiderInetdiskBase


class SpiderBaiduInetdisk(SpiderInetdiskBase):

    def __init__(self, task, appcfg, clientid):
        super(SpiderBaiduInetdisk, self).__init__(task, appcfg, clientid)
        self.userid = ''
        if self.task.cookie and self.task.tokentype.value == 4:
            self._ha._managedCookie.add_cookies('.baidu.com', self.task.cookie)

    def _cookie_login(self):
        try:
            url = 'https://pan.baidu.com/disk/home?errno=0&errmsg=Auth%20Login%20Sucess&&bduss=&ssnerror=0&traceid='
            html = self._ha.getstring(url, headers="""
                        Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
                        Accept-Encoding: gzip, deflate, br
                        Accept-Language: zh-CN,zh;q=0.9
                        Cache-Control: no-cache
                        Connection: keep-alive
                        Host: pan.baidu.com
                        Pragma: no-cache
                        Referer: https://pan.baidu.com/disk/home?errno=0&errmsg=Auth%20Login%20Sucess&&bduss=&ssnerror=0&traceid=
                        Upgrade-Insecure-Requests: 1
                        User-Agent: netdisk;6.7.1.9;PC;PC-Windows;10.0.17763;WindowsBaiduYunGuanJia""")
            self.userid = re.findall(r"initPrefetch\('.*?', '(.*?)'\);", html)[0]
            return True
        except:
            return False

    def _get_folder(self):
        self.__get_token_sign()
        path = "/"
        dirlist, url = self._get_dir(path)
        if dirlist:
            self._root = INETDISKFILELIST(self._clientid, self.task, self._appcfg._apptype, self.userid, 'root', url,
                                          'root', path)
            return dirlist, url, self._root

    def __get_sign(self, sign1, sign3):
        try:
            js = """
            function s(j,r){var a=[];var p=[];var o="";var v=j.length;for(var q=0;q<256;q++){a[q]=j.substr((q%v),1).charCodeAt(0);p[q]=q}for(var u=q=0;q<256;q++){u=(u+p[q]+a[q])%256;var t=p[q];p[q]=p[u];p[u]=t}for(var i=u=q=0;q<r.length;q++){i=(i+1)%256;u=(u+p[i])%256;var t=p[i];p[i]=p[u];p[u]=t;k=p[((p[i]+p[u])%256)];o+=String.fromCharCode(r.charCodeAt(q)^k)}return o};
            base64Encode=function(t) {
                        var e, r, a, o, n, i, s = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
                        for (a = t.length,
                        r = 0,
                        e = ""; a > r; ) {
                            if (o = 255 & t.charCodeAt(r++),
                            r == a) {
                                e += s.charAt(o >> 2),
                                e += s.charAt((3 & o) << 4), 
                                e += "==";
                                break
                            }
                            if (n = t.charCodeAt(r++),
                            r == a) {
                                e += s.charAt(o >> 2),
                                e += s.charAt((3 & o) << 4 | (240 & n) >> 4),
                                e += s.charAt((15 & n) << 2),
                                e += "=";
                                break
                            }
                            i = t.charCodeAt(r++),
                            e += s.charAt(o >> 2),
                            e += s.charAt((3 & o) << 4 | (240 & n) >> 4),
                            e += s.charAt((15 & n) << 2 | (192 & i) >> 6),
                            e += s.charAt(63 & i)
                        }
                        return e
                    }"""
            ctx = execjs.compile(js)
            res = ctx.call('s', sign3, sign1)
            bs64res = ctx.call('base64Encode', res)
            return bs64res
        except Exception:
            self._logger.error('Got sign fail: {}'.format(traceback.format_exc()))

    def __get_logid(self):
        try:
            t = str(int(datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() * 1000)) + '0'
            i = '.' + str(random.randint(1000000000000000, 10000000000000000))
            t = t + i
            # 生成一个md5对象
            m1 = hashlib.md5()
            # 使用md5对象里的update方法md5转换
            m1.update(t.encode("utf-8"))
            logid = m1.hexdigest()
            return logid
        except Exception:
            self._logger.error('Got logid fail: {}'.format(traceback.format_exc()))

    def __get_token_sign(self):
        try:
            url = 'https://pan.baidu.com/disk/home?errno=0&errmsg=Auth%20Login%20Sucess&&bduss=&ssnerror=0&traceid='
            html = self._ha.getstring(url, headers="""
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
            Accept-Encoding: gzip, deflate, br
            Accept-Language: zh-CN,zh;q=0.9
            Cache-Control: no-cache
            Connection: keep-alive
            Host: pan.baidu.com
            Pragma: no-cache
            Referer: https://pan.baidu.com/disk/home?errno=0&errmsg=Auth%20Login%20Sucess&&bduss=&ssnerror=0&traceid=
            Upgrade-Insecure-Requests: 1
            User-Agent: netdisk;6.7.1.9;PC;PC-Windows;10.0.17763;WindowsBaiduYunGuanJia""")
            global token, timestamp, sign
            token = substring(html, "initPrefetch('", "'")
            timestamp = substring(html, '"timestamp":', ',')
            sign1 = substring(html, '"sign1":"', '"')
            sign3 = substring(html, '"sign3":"', '"')
            sign = self.__get_sign(sign1, sign3)
            if not token or not sign:
                self._logger.info('Got sign or token is None')
        except Exception:
            self._logger.error('Got sign and token fail: {}'.format(traceback.format_exc()))
        # return token

    def _get_dir(self, path):
        try:
            logid = self.__get_logid()
            page = 0
            dirlist = []
            while True:
                page += 1
                dpath = quote_plus(path)
                url = f'https://pan.baidu.com/api/list?dir={dpath}&channel=chunlei&web=1&app_id=250528&num=100&order=time&desc=1' \
                      f'logid={logid}&clienttype=0&showempty=0&web=1&page={page}&bdstoken={token}'

                html = self._ha.getstring(url, headers="""
        Accept: */*
        Accept-Encoding: gzip, deflate, br
        Accept-Language: zh-CN,zh;q=0.9
        Cache-Control: no-cache
        Connection: keep-alive
        Host: pan.baidu.com
        Pragma: no-cache
        Referer: https://pan.baidu.com/disk/home?errno=0&errmsg=Auth%20Login%20Sucess&&bduss=&ssnerror=0&traceid=
        User-Agent: netdisk;6.7.1.9;PC;PC-Windows;10.0.17763;WindowsBaiduYunGuanJia""")
                jshtml = json.loads(html)
                dirs = jshtml['list']
                if dirs:
                    for i in dirs:
                        dirlist.append(i)
                if len(jshtml['list']) < 100:
                    break
            return dirlist, url
        except Exception:
            self._logger.error('Got "{}" dir fail: {}'.format(path, traceback.format_exc()))

    def _dirs_list(self, dirlist, url, root):
        try:
            for m in dirlist:
                isdir = m['isdir']
                treedataid = m['fs_id']
                path = m['path']
                if isdir == 1:
                    name = m['server_filename']
                    one = INETDISKFILELIST(self._clientid, self.task, self._appcfg._apptype, self.userid, treedataid, url, name, path)
                    jshtml, url = self._get_dir(path)
                    self._dirs_list(jshtml, url, one)
                    self._logger.info('Path:{} -dir have appended success.'.format(path))
                    root.append_item(one)
                elif isdir == 0:
                    num = 0
                    while True:
                        try:
                            downloadurl, stream_io = self._download_file(treedataid)
                            break
                        except:
                            num += 1
                            self.__get_token_sign()
                            time.sleep(2)
                            if num == 5:
                                b = '内容暂时无法下载！'
                                downloadurl = f'https://pan.baidu.com{path}'
                                stream_io = io.StringIO(b)
                                break
                    downloadurl = downloadurl
                    filename = m['server_filename']
                    filesize = m['size']

                    file_one = INETDISKFILE(self._clientid, self.task, self._appcfg._apptype, treedataid, path, downloadurl, stream_io, filename, filesize)
                    file_one.skydrivetype="百度网盘"
                    self._logger.info('Path:{} -file have appended success'.format(path))
                    root.append_item(file_one)

                    yield file_one

        except Exception:
            self._logger.error('Got file {} fail: {}'.format(root.path, traceback.format_exc()))

    def _download_file(self, treedataid):
        try:
            logid = self.__get_logid()
            t = int(datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() * 1000)
            s = quote_plus(sign)
            url = f'https://pan.baidu.com/api/download?sign={s}&timestamp={timestamp}&fidlist=%5B{treedataid}%5D&type=dlink' \
                  f'&vip=0&channel=chunlei&web=1&app_id=250528&dstoken={token}&logid={logid}&clienttype=0&startLogTime={t}'
            html = self._ha.getstring(url, headers="""
        Accept: application/json, text/javascript, */*; q=0.01
        Accept-Encoding: gzip, deflate, br
        Accept-Language: zh-CN,zh;q=0.9
        Cache-Control: no-cache
        Connection: keep-alive
        Host: pan.baidu.com
        Pragma: no-cache
        Referer: https://pan.baidu.com/disk/home?errno=0&errmsg=Auth%20Login%20Sucess&&bduss=&ssnerror=0&traceid=
        User-Agent: netdisk;6.7.1.9;PC;PC-Windows;10.0.17763;WindowsBaiduYunGuanJia""")
            jshtml = json.loads(html)
            downloadurl = jshtml['dlink'][0]['dlink']
            html, redir = self._ha.getstring_unredirect(downloadurl)
            resp = self._ha.get_response(redir, stream=True)
            return redir, resp.raw
        except Exception:
            print('Download {} file fail: {}'.format(treedataid, traceback.format_exc()))
