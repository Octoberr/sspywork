"""
获取163邮箱的信息
createby swm 2018/05/28
"""
import requests


class MAIL:

    def __init__(self):
        self.cookie = 'starttime=; NTES_SESS=lAolQIaSvwx4joVXa5ael_S.ZhzwVmAaBJSvUxvzO5cs5EnP5.MfeYnPhSGf_RQExrcRLoac6vuX1.59RgAiZUSQj8JRmyvRtn8dePsyd_Y4E4iWDm6mj7eoRh3mlOfOvE57Piw_Xv9JdVbqWEzQurnURsr1u8w.a8bXjW0RNofisNsZzMX.H5_Km8iJmnIlOST0AVuneZGsY; NTES_PASSPORT=OPxQp7anLbnaydkDAzFfBi9qS3cQ5O51jaJGTezuvHwBhziQhoRng7iQ93mnksyzAROLI0056AEDikRWI1uFUF0XROWQv4LdsAsxMmLwINDljM.q_fAF79SCE1QMfRKSEtw8ST5QByefiZxToxjuHPJ0XjRQq0Q2KBvSCwMMfdaC1iqWC7gwA9Qsn; S_INFO=1527496536|0|2&70##|nmsb12345; P_INFO=nmsb12345@163.com|1527496536|1|mail163|00&99|sic&1527059755&mail163#sic&510100#10#0#0|&0|mail163|nmsb12345@163.com; mail_upx=c1bj.mail.163.com|c2bj.mail.163.com|c3bj.mail.163.com|c4bj.mail.163.com|c5bj.mail.163.com|c6bj.mail.163.com|c7bj.mail.163.com; mail_upx_nf=; mail_idc=; Coremail=f0e9fff361364%ABKmxVpvrziIvaGAOTvvxCUhMuOjYABv%g6a49.mail.163.com; MAIL_MISC=nmsb12345; cm_last_info=dT1ubXNiMTIzNDUlNDAxNjMuY29tJmQ9aHR0cCUzQSUyRiUyRm1haWwuMTYzLmNvbSUyRm0lMkZtYWluLmpzcCUzRnNpZCUzREFCS214VnB2cnppSXZhR0FPVHZ2eENVaE11T2pZQUJ2JnM9QUJLbXhWcHZyemlJdmFHQU9UdnZ4Q1VoTXVPallBQnYmaD1odHRwJTNBJTJGJTJGbWFpbC4xNjMuY29tJTJGbSUyRm1haW4uanNwJTNGc2lkJTNEQUJLbXhWcHZyemlJdmFHQU9UdnZ4Q1VoTXVPallBQnYmdz1tYWlsLjE2My5jb20mbD0wJnQ9MTEmYXM9ZmFsc2U=; MAIL_SESS=lAolQIaSvwx4joVXa5ael_S.ZhzwVmAaBJSvUxvzO5cs5EnP5.MfeYnPhSGf_RQExrcRLoac6vuX1.59RgAiZUSQj8JRmyvRtn8dePsyd_Y4E4iWDm6mj7eoRh3mlOfOvE57Piw_Xv9JdVbqWEzQurnURsr1u8w.a8bXjW0RNofisNsZzMX.H5_Km8iJmnIlOST0AVuneZGsY; MAIL_SINFO=1527496536|0|2&70##|nmsb12345; MAIL_PINFO=nmsb12345@163.com|1527496536|1|mail163|00&99|sic&1527059755&mail163#sic&510100#10#0#0|&0|mail163|nmsb12345@163.com; secu_info=1; mail_entry_sess=172fb500146ef66a89d4f1c6517576340b746cf5fa6caed414b19e02741e4b4a879839690719953cc7c44442fb9f44c4b4ee4ea0f841a965c606edf9475487f027f420bc195eb8c2650f46f643ebeaa02d306b9edcb9be44c6e8137384f9965159a9a62cd35539b55a1818782d3238a31ab6ed5dd3b3217bdadacc9947e13d868b32f753ae54455277cbdc1844a80176030200a6f8b7ca4cc40c8954516cf8420169cedb3e8b119845948a418360c406e147f1771ffadc7731a8635977da6f19; JSESSIONID=E87F59C2993D54CACC72CB24B5FF68CE'
        self.usragent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
        self.headers = {
            "Cookie": self.cookie,
            "User-Agent": self.usragent
        }
        self.data = {
            "var": '<?xml version="1.0"?><object><array name="items"><object><string name="func">mbox:getAllFolders</string><object name="var"><boolean name="stats">true</boolean></object></object><object><string name="func">mbox:listMessages</string><object name="var"><string name="order">date</string><boolean name="desc">true</boolean><int name="start">0</int><int name="limit">20</int><int name="fid">1</int></object></object></array></object>'
        }

    def getmailinfo(self):
        # 获取邮件列表
        url = 'http://mail.163.com/m/s?sid=ABKmxVpvrziIvaGAOTvvxCUhMuOjYABv&func=global:sequential'
        data = requests.post(url, headers=self.headers, data=self.data)
        print(data.text)

    def getmailcontent(self):
        # 获取邮件内容
        url = 'http://mail.163.com/m/s?sid=ABKmxVpvrziIvaGAOTvvxCUhMuOjYABv&func=mbox:readMessage&l=read&action=read&l=read&action=read&l=read&action=read'
        cdata = {
            "var": '<?xml version="1.0"?><object><string name="id">467:xtbB0xuKWVXlbYVBGwAAsZ</string><string name="mode">both</string><boolean name="autoName">true</boolean><boolean name="supportTNEF">true</boolean><boolean name="filterStylesheets">true</boolean><boolean name="returnImageInfo">true</boolean></object>'
        }
        data = requests.post(url, headers=self.headers, data=cdata)
        print(data.text)


if __name__ == '__main__':
    mm = MAIL()
    mm.getmailcontent()
