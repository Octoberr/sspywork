"""
获取qq空间的信息
create by swm
2018/05/30
"""

import requests
import json


class MAIL:

    def __init__(self):
        self.cookie = '_qz_referrer=qzone.qq.com; pgv_pvi=6901643264; pgv_si=s824218624; ptisp=cnc; pt2gguin=o1353480158; uin=o1353480158; skey=@IaUZCJPwl; RK=5tjoTivgTd; ptcz=92cab460d0d2484f2d33b32b40d46edfe1c692bb28c40aa5d81024ab23a87c28; p_uin=o1353480158; pt4_token=2vVYenT-cmA38OjPjZminHGkqDxah-AnI2WrSDzEz7o_; p_skey=MVevSZKVGP6kWhEqTOWDPdRjVimibFjMAS5PdswSraQ_'
        self.usr = 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
        self.headers = {
            'cookie': self.cookie,
            'user-agent': self.usr
        }

    def getpersonalinfo(self):
        # 获取个人信息
        url = 'https://mobile.qzone.qq.com/profile_get?g_tk=130299389&format=json&hostuin=1353480158'
        data = requests.get(url, headers=self.headers)
        res = json.loads(data.text)
        print(res['data'])
        # print(data.text)

    def getfriends(self):
        # 获取好友列表
        url = 'https://mobile.qzone.qq.com/friend/mfriend_list?g_tk=130299389&res_uin=1353480158&res_type=normal&format=json&count_per_page=10&page_index=0&page_type=0&mayknowuin=&qqmailstat='
        data = requests.get(url, headers=self.headers)
        res = json.loads(data.text)
        print(res['data']['list'])
        # print(data.text)

    def getqzonelogs(self):
        # 获取空间日志
        url = 'https://h5.qzone.qq.com/webapp/json/mqzone_feeds/getActiveFeeds?qzonetoken=218cdbd60c0c870173e4d348cebf878f03b87d4c2e5d19b8a23d9e413abf18b5124257454b1deb40c636039c44d468d2ce&g_tk=130299389'
        pdata = {
            'res_type': '0',
            'res_attach': 'back_server_info=basetime%3D1527520201%26pagenum%3D2%26dayvalue%3D2%26getadvlast%3D0%26hasgetadv%3D%26lastentertime%3D1527649814%26LastAdvPos%3D0%26UnReadCount%3D0%26UnReadSum%3D-1%26LastIsADV%3D0%26UpdatedFollowUins%3D%26UpdatedFollowCount%3D0%26LastRecomBrandID%3D&lastrefreshtime=1527649817&lastseparatortime=0&loadcount=0',
            'refresh_type': '2',
            'format': 'json',
            'attach_info': 'ack_server_info=basetime%3D1527520201%26pagenum%3D2%26dayvalue%3D2%26getadvlast%3D0%26hasgetadv%3D%26lastentertime%3D1527649814%26LastAdvPos%3D0%26UnReadCount%3D0%26UnReadSum%3D-1%26LastIsADV%3D0%26UpdatedFollowUins%3D%26UpdatedFollowCount%3D0%26LastRecomBrandID%3D&lastrefreshtime=1527649817&lastseparatortime=0&loadcount=0'
        }
        res = requests.post(url, headers=self.headers, data=pdata)
        resdic = json.loads(res.text)
        print(resdic['data']['vFeeds'])
        # print(res.text)

    def getqzonephots(self):
        # 获取qq空间的相册列表
        url = 'https://mobile.qzone.qq.com/list?g_tk=130299389&format=json&list_type=album&action=0&res_uin=1353480158&count=10'
        res = requests.get(url, headers=self.headers)
        print(res.text)

    def getphotos(self):
        url = 'https://h5.qzone.qq.com/webapp/json/mqzone_photo/getPhotoList2?g_tk=130299389&uin=1353480158&albumid=V13D89lC1ismHx&ps=0&pn=20&password=&password_cleartext=0&swidth=1125&sheight=2436'
        res = requests.get(url, headers=self.headers)
        print(res.text)


if __name__ == '__main__':
    # MAIL().getpersonalinfo()
    # MAIL().getfriends()
    # MAIL().getqzonelogs()
    # MAIL().getqzonephots()
    MAIL().getphotos()
