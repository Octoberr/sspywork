"""
获取126企业邮箱的信息
create by swm 2018/05/28
"""
import requests


class MAIL:

    def __init__(self):
        self.cookie = 'starttime=; NTES_SESS=jCvK1n47d2N1H1PVmBJMJJnOD2w4yhE7RJSvUxvzO5cs5EnP5.MfeYnPhSGf_RQExsXlllj49nZzDL5Yp_Mq_N4ks8gM2x5.nVPlnoY97fQmfWCSGGLrEiv33hjRRKvROsx3bo0d0OgZP9.p8rnDt1PpJpwG9t9wwJE5OFjX44RgcibnbH6.Bo8.QRa25okXDJ065zXcpKXzScWb9TTGKj0hQ; NTES_PASSPORT=eaF6UHm9zFQ_tX0p.15wi9ACuFzJXl2YaintMs4Kl_TOv4jcvh2dqAjc6FLdePH40QBWWWxofjMgFy4JVcuKBcNxSGu8d3O6RGNSR6v.nJYRiYFOk8XVJq9axzrrdbJKrtc7XshaCeltjstpohfckrMwAmZVs0epot9.kOGK6Xy_DA31gyIQK1w7nOVrF33M2; S_INFO=1527500681|0|#2&70#|nmsb1234567@126.com; P_INFO=nmsb1234567@126.com|1527500681|1|mail126|00&99|null&null&null#sic&510100#10#0#0|&0||nmsb1234567@126.com; mail_upx=c2bj.mail.126.com|c3bj.mail.126.com|c4bj.mail.126.com|c5bj.mail.126.com|c6bj.mail.126.com|c7bj.mail.126.com|c1bj.mail.126.com; mail_upx_nf=; mail_idc=; Coremail=020e7c7a966c0%GBzraFkziijnzkixdizzxNvvjTvaoyPW%g1a49.mail.126.com; MAIL_MISC=nmsb1234567@126.com; cm_last_info=dT1ubXNiMTIzNDU2NyU0MDEyNi5jb20mZD1odHRwJTNBJTJGJTJGbWFpbC4xMjYuY29tJTJGbSUyRm1haW4uanNwJTNGc2lkJTNER0J6cmFGa3ppaWpuemtpeGRpenp4TnZ2alR2YW95UFcmcz1HQnpyYUZremlpam56a2l4ZGl6enhOdnZqVHZhb3lQVyZoPWh0dHAlM0ElMkYlMkZtYWlsLjEyNi5jb20lMkZtJTJGbWFpbi5qc3AlM0ZzaWQlM0RHQnpyYUZremlpam56a2l4ZGl6enhOdnZqVHZhb3lQVyZ3PW1haWwuMTI2LmNvbSZsPTAmdD0xMSZhcz1mYWxzZQ==; MAIL_SESS=jCvK1n47d2N1H1PVmBJMJJnOD2w4yhE7RJSvUxvzO5cs5EnP5.MfeYnPhSGf_RQExsXlllj49nZzDL5Yp_Mq_N4ks8gM2x5.nVPlnoY97fQmfWCSGGLrEiv33hjRRKvROsx3bo0d0OgZP9.p8rnDt1PpJpwG9t9wwJE5OFjX44RgcibnbH6.Bo8.QRa25okXDJ065zXcpKXzScWb9TTGKj0hQ; MAIL_SINFO=1527500681|0|#2&70#|nmsb1234567@126.com; MAIL_PINFO=nmsb1234567@126.com|1527500681|1|mail126|00&99|null&null&null#sic&510100#10#0#0|&0||nmsb1234567@126.com; secu_info=1; mail_entry_sess=0eff28265b0c73c8ebfb434b076a1f01bb6292d3e7f3799e7ecbd142e2f5bb2a6c218f261663d5ecfa6db9547a0e5a798c8ce795702393dfc0a78a08f839942744d0bedc0d4b243bd02cbfa30a8030fc9d8ac6253ecbbf02a6aa1f8f2c6cf1ef50a0ec368cc77dfd8811934601ae820851f3206b9c30a026d5f212f3331476d99f8d8e1f8a4fbec27fd744dc1d862b8e73e7168c2ba92338c1b416c0044185673ae59a122aad000961cc47f10192a66fa77f05487f50003ac1b9125527901f57; JSESSIONID=0CF572B80519B1E0F1067C99DA49046B; locale='
        self.usangent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
        self.headers = {
            "Cookie": self.cookie,
            "User-Agent": self.usangent
        }

    def getmaillist(self):
        # 获取邮件列表
        url = 'http://mail.126.com/m/s?sid=GBzraFkziijnzkixdizzxNvvjTvaoyPW&func=global:sequential'
        formdata = {
            'var': '<?xml version="1.0"?><object><array name="items"><object><string name="func">mbox:getAllFolders</string><object name="var"><boolean name="stats">true</boolean></object></object><object><string name="func">mbox:listMessages</string><object name="var"><string name="order">date</string><boolean name="desc">true</boolean><int name="start">0</int><int name="limit">20</int><int name="fid">1</int></object></object></array></object>'
        }
        res = requests.post(url, headers=self.headers, data=formdata)
        print(res.text)

    def getmailcontent(self):
        # 获取邮件信息
        url = 'http://mail.126.com/m/s?sid=GBzraFkziijnzkixdizzxNvvjTvaoyPW&func=mbox:readMessage&l=read&action=read'
        formdata = {
            "var": '<?xml version="1.0"?><object><string name="id">244:1tbi9Auh6VYY9gHy-AAAsA</string><string name="mode">both</string><boolean name="autoName">true</boolean><boolean name="supportTNEF">true</boolean><boolean name="filterStylesheets">true</boolean><boolean name="returnImageInfo">true</boolean></object>'
        }
        res = requests.post(url, headers=self.headers, data=formdata)
        print(res.text)


if __name__ == '__main__':
    m = MAIL()
    m.getmailcontent()