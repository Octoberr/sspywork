"""
获取qq邮箱的信息
createby swm 2018/05/28
"""
import requests
from bs4 import BeautifulSoup
import demjson


class MAILQQ:

    def __init__(self):
        self.qqurl = 'https://w.mail.qq.com'
        self.starturl = 'https://w.mail.qq.com/cgi-bin/mobile?sid=57gHkw9Q1J6VeDRvfKDQO-Ct,4,qMUhsSDR4WERsMUxCVVZHKkctMXZEdW5MTkJ3SUlpY0I1ZERyaWxtNTZVWV8.&t=phone'
        self.cookie = 'mcookie=0&y; pgv_pvi=6954055680; pgv_si=s8512669696; ptisp=cnc; pt2gguin=o1279958111; uin=o1279958111; skey=@Z4vYLgJ7g; RK=5r59A+8QTV; ptcz=6ccd43ac1dc28bd976155865a80839f54d0866433603b59879321af0d726e380; p_uin=o1279958111; pt4_token=huhVEgiwG9bhiMAa8KltiUKcYQslq-aykpVkOaclYfo_; p_skey=1HlH4xXDl1LBUVG*G-1vDunLNBwIIicB5dDrilm56UY_; qm_flag=0; qqmail_alias=sldjlv@qq.com; msid=57gHkw9Q1J6VeDRv0F7TgfMX,4,qMUhsSDR4WERsMUxCVVZHKkctMXZEdW5MTkJ3SUlpY0I1ZERyaWxtNTZVWV8.; sid=1279958111&43f146fded08a53e50b69c6dd2a00c61,qMUhsSDR4WERsMUxCVVZHKkctMXZEdW5MTkJ3SUlpY0I1ZERyaWxtNTZVWV8.; qm_username=1279958111; ssl_edition=sail.qq.com; edition=mail.qq.com; username=1279958111&1279958111; qm_sk=1279958111&fKDQO-Ct; device=phone; promote_iphone=0; new_mail_num=1279958111&4; qm_ssum=1279958111&431144748c75ff98985bed476f61d958'
        self.useragent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'accept-language',
            'cache-control': 'max-age=0',
            'user-agent': self.useragent,
            'cookie': self.cookie
        }

    def cookielogin(self):
        # 使用cookie登陆
        html = requests.get(self.starturl, headers=self.headers)
        html.encoding = 'utf-8'
        print(html.text)

    def loginstatus(self):
        reurl = 'https://w.mail.qq.com/cgi-bin/help_static_login?sid=57gHkw9Q1J6VeDRvfKDQO-Ct,4,qMUhsSDR4WERsMUxCVVZHKkctMXZEdW5MTkJ3SUlpY0I1ZERyaWxtNTZVWV8.&t=help_static_login&page=1&type=0'
        html = requests.get(reurl, headers=self.headers)
        html.encoding = 'utf-8'
        souphtml = BeautifulSoup(html.text, 'lxml')
        # 登陆表格
        # allscripts = souphtml.find('table', class_='qm_table loginlog_table')
        # print(allscripts)
        # 下一页链接
        nextpage = souphtml.find('a', class_='qm_page_item', title='下一页')
        link = nextpage.get('href')
        print(self.qqurl+link)

    def getcontact(self):
        # 邮箱联系人
        curl = 'https://mail.qq.com/cgi-bin/addr_listall?sid=57gHkw9Q1J6VeDRvfKDQO-Ct&encode_type=js&show_type=hot&all_data=1&level=0&qq=0&t=addr_jsonp.json&sorttype=Freq&s=AutoComplete&category=hot&record=n&resp_charset=UTF8&ef=js&hot=1&cb=addr_callback'
        data = requests.get(curl, headers=self.headers)
        res = data.text
        strjson = res[14:-1]
        dict = demjson.decode(strjson)
        print(dict['sortbyupdatetime'])
        print(type(dict['sortbyupdatetime']))
        # print(type(dict))

    def getmail(self):
        # 获取qq邮箱邮件的内容
        murl = 'https://w.mail.qq.com/cgi-bin/mail_list?ef=js&r=0.08954836337283911&sid=qfawjxO4C0FKTwNYfKDQO-Ct,4,qYndjb2xaSmpDblhFWEl0M004VDhXeVZaWjZsdioyS0ZjT0h6bFpqKnc3d18.&t=mobile_data.json&s=list&cursor=max&cursorutc=1520574283&cursorid=ZC0509-VwhD~GR7560PFVkDsf6DO83&cursorcount=20&folderid=1&device=ios&app=phone&ver=app'
        data = requests.get(murl, headers=self.headers)
        res = data.text.strip()
        resdict = demjson.decode(res)
        print(resdict['mls'])


if __name__ == '__main__':
    qq = MAILQQ()
    qq.getmail()