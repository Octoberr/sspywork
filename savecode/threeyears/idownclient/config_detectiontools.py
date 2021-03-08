"""
将侦查工具与数据类型对应起来
create by swm 2019/09/24
"""


class DetecTools(object):
    def __init__(self):
        # 1、子域名挖掘
        self.subdomain = '子域名挖掘'
        # 2、域名解析
        self.ip_history = '域名解析'
        # 3、真实ip探测
        self.real_ip = '真实IP探测'
        # 4、Whois查询
        self.whois = 'Whois查询'
        # 5、域名注册查询
        self.whois_reverse = '域名注册查询'
        # 6、资产侦测雷达
        self.service = '资产侦测雷达'
        # 7、URL枚举
        self.urlenum = 'URL枚举'
        # 8、URL信息探测
        self.urlInfo = 'URL信息探测'
        # 9、IP反查域名
        self.domain_detec = 'IP反查域名'
        # 10、历史绑定域名
        self.domain_history = '历史绑定域名'
        # 11、旁站探测
        self.side_site_detect = '旁站探测'
        # 12、C段存活探测
        self.rangec_detect = 'C段存活探测'
        # 13、IP归属地查询
        self.location = 'IP归属地查询'
        # 14、ISP供应商查询
        self.ipwhois = 'IP Whois信息'
        # 15、目标防护探测
        self.waf_detect = '目标防护探测'
        # 16、邮服定位
        self.mail_server = '邮服定位'
        # 17、邮箱搜集
        self.email = '邮箱搜集'
        # 18、电话号码搜集
        self.phone = '电话号码搜集'
        # 19、Google搜索引擎
        self.google = 'Google搜索引擎'
        # 20、Bing搜索引擎
        self.bing = 'Bing搜索引擎'
        # 21、Baidu搜索引擎
        self.baidu = 'Baidu搜索引擎'
        # 22、Github
        self.github = 'Github'
        # 23、客户端环境刺探
        self.payload_clients = '客户端环境刺探'
        # 24、回旋式辅助定位
        self.payload_location = '回旋式辅助定位'
        # 25、淘宝账号跨域刺探
        self.payload_taobao = '淘宝账号跨域刺探'
        # 26、大众点评账号跨域刺探
        self.payload_dianping = '大众点评账号跨域刺探'
        # 27、新浪微博账号跨域刺探
        self.payload_microblog = '新浪微博账号跨域刺探'
        # 28、去哪儿账号跨域刺探
        self.payload_qunaer = '去哪儿账号跨域刺探'
        # 29、天涯论坛账号跨域刺探
        self.payload_tianya = '天涯论坛账号跨域刺探'
        # 30、百度账号跨域刺探
        self.payload_baidu = '百度账号跨域刺探'
        # 31、搜狐账号跨域刺探
        self.payload_souhu = '搜狐账号跨域刺探'
        # 32、Telegram社交身份落地核查
        self.landing_telegram = 'Telegram社交身份落地核查'
        # 33、Messager社交身份落地核查
        self.landing_messenger = 'Messenger社交身份落地核查'
        # 34、微信社交身份落地核查
        self.landing_wechat = '微信社交身份落地核查'
        # 35、facebook 社交身份落地核查
        self.landing_facebook = 'Facebook社交身份落地核查'
        # 36、twitter 社交身份落地核查
        self.landing_twitter = 'Twitter社交身份落地核查'
        # 37、instagram 社交身份落地核查
        self.landing_instagram = 'Instagram社交身份落地核查'
        # 38、Telegram群/频道监测
        self.public_telegram = 'Telegram群/频道监测'
        # 39、Facebook动态监测
        self.public_facebook = 'Facebook动态监测'
        # 40、Twitter动态监测
        self.public_twitter = 'Twitter动态监测'
        # 41、Linkedln动态监测
        self.public_linkedin = 'LinkedIn动态监测'
        # 42、Instgram动态监测
        self.public_instgram = 'Instgram动态监测'


dtools = DetecTools()
