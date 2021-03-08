"""
idown下载策略默认值
"""

# 循环下载的时间间隔，单位:分钟, 默认3小时
# cookie的保活时间，单位：分钟，默认15分钟
# 收邮时间段开始时间
# 收邮时间段结束时间
# 收取的邮件时间范围,单位：天，默认无限制
# 收取邮件的大小设置，单位：M，默认无限制
# 设置收取收件箱邮件的个数限制，默认无限制
# 设置收取草稿箱邮件的个数限制, 默认无限制
# 设置收取已发送邮件个数限制，默认无限制
# 设置收取已删除邮件个数限制，默认无限制
# 设置收取垃圾箱邮件个数限制，默认无限制
# 设置收取邮件的最大失败数,单位：个，默认为10个
# 设置邮件协议优先级,有3种，webmail,pop3,imap
# 默认的通用配置
# 时间单位全部换算成秒，便于直接计算
# 通用的配置入数据库后慢慢写吧
# 下载启停控制
switch_control = {"download_switch": 1, "monitor_switch": 1}
# --------------------------通用下载设置

# circulation_mode默认一次性任务为1，周期任务为2

stratagy = {
    "type": "idown",
    "circulation_mode": 1,
    "time_start": None,
    "time_end": None,
    "concur_num": 5,
    "interval": 3 * 60 * 60,
    "period": [],
    "cookie_keeplive": 15 * 60,
    "data_limit_time": -1,
    "data_limit_size": -1,
    "priority": 2,
}
# #-------------------------------------------------------------
# 针对邮箱下载的默认配置,邮箱下载数量的限制
# 邮箱过滤自己添加，失败次数
stratagymail = {
    "eml_download_limit": {},
    "eml_folders_filter": [],
    "eml_failures_times": 10,
    "eml_priority_protocol": "webmail",
}

# -------------------------------------------------------------
# 侦查相关设置
enable = 0
stratagyscout = {
    "recursion_level": 1,  # 结束的level
    "start_level": 1,  # 开始的level
    "default_ports": [20, 21, 22, 23, 25, 53, 80, 110, 143, 443, 3389, 8080],
    "relationfrom": None,  # 这个值是界面给的，所以如果界面那边没有的话也不用更新了
    "domain": {
        "function": {
            "subdomain": enable,
            "ip_history": enable,
            "whois": enable,
            "email": enable,
            "phone": enable,
            "search_google": enable,
            "search_bing": enable,
            "search_baidu": enable,
            "url": enable,
            "service": enable,
            "real_ip": enable,
            "side_site_detect": enable,
            "waf_detect": enable,
            "mail_server": enable,
        },
        "searchengine": {
            "search_google": {"keywords": [], "filetypes": []},
            "search_bing": {"keywords": [], "filetypes": []},
            "search_baidu": {"keywords": [], "filetypes": []},
        },
        "ports": [
            20,
            21,
            22,
            23,
            25,
            53,
            80,
            110,
            123,
            143,
            443,
            993,
            995,
            1433,
            3389,
            6379,
            8080,
            27017,
        ],
    },
    "ip": {
        "function": {
            "domain_detect": enable,
            "domain_history": enable,
            "location": enable,
            "ipwhois": enable,
            "url": enable,
            "service": enable,
            "side_site_detect": enable,
            "rangec_detect": enable,
        },
        "ports": [
            20,
            21,
            22,
            23,
            25,
            53,
            80,
            110,
            123,
            143,
            443,
            993,
            995,
            1433,
            3389,
            6379,
            8080,
            27017,
        ],
    },
    "url": {
        "function": {
            "homepage_code": 1,
            "summary": 1,
            "homepage_screenshot": 1,
            "components": 1,
            "waf_detect": 1,
        }
    },
    "email": {
        "function": {
            "mail_server": enable,
            "whois_reverse": enable,
            "phone": enable,
            "search_google": enable,
            "search_bing": enable,
            "search_baidu": enable,
            "landing_facebook": enable,
            "landing_messenger": enable,
        },
        "searchindex": {
            "landing_facebook": {"start": 0, "stop": 10}
            # 后面可能会添加其他的
        },
        "posttime": {
            "public_facebook": {
                "start": "2019-09-10 00:00:00",
                "stop": "2019-09-10 00:00:00",
            },
            "searchengine_keywords": [],
            "searchengine_filetypes": [],
        },
        "searchengine": {
            "search_google": {"keywords": [], "filetypes": []},
            "search_bing": {"keywords": [], "filetypes": []},
            "search_baidu": {"keywords": [], "filetypes": []},
        },
    },
    "phone": {
        "function": {
            "whois_reverse": enable,
            "email": enable,
            "search_google": enable,
            "search_bing": enable,
            "search_baidu": enable,
            "landing_messenger": enable,
            "landing_telegram": enable,
            "public_telegram": enable,
        },
        "searchindex": {"landing_facebook": {"start": 0, "stop": 10}},
        "posttime": {
            "public_telegram": {
                "start": "2019-09-10 00:00:00",
                "stop": "2019-09-10 00:00:00",
            }
        },
        "searchengine": {
            "search_google": {"keywords": [], "filetypes": []},
            "search_bing": {"keywords": [], "filetypes": []},
            "search_baidu": {"keywords": [], "filetypes": []},
        },
    },
    "networkid": {
        "function": {
            "whois_reverse": enable,
            "search_google": enable,
            "search_bing": enable,
            "search_baidu": enable,
            "email": enable,
            "phone": enable,
            "landing_facebook": enable,
            "landing_twitter": enable,
            "landing_linkedin": enable,
            "landing_instgram": enable,
            "public_facebook": enable,
            "public_twitter": enable,
            "public_linkedin": enable,
            "public_instgram": enable,
        },
        # 'netidinfo': [{'source': 'default', 'userid': None, 'url': None}],
        "netidinfo": [],
        "searchindex": {
            "landing_facebook": {"start": 0, "stop": 10},
            "landing_twitter": {"start": 0, "stop": 10},
        },
        "posttime": {"public_twitter": {"timerange": 30}},
        "searchengine": {
            "search_google": {"keywords": [], "filetypes": []},
            "search_bing": {"keywords": [], "filetypes": []},
            "search_baidu": {"keywords": [], "filetypes": []},
        },
    },
}
# ----------------------------------------------------------
# 扫描设置
stratagyscan = {
    "scan": {
        "hosts": [],
        "location": None,
        "ports": [20, 21, 22, 23, 25, 53, 80, 110, 143, 443, 3389, 8080],
        "vuls": [],
    },
    "search": {
        "count": 100,
        "index": 1,
        "filter": {
            "app": None,
            "ver": None,
            "device": None,
            "os": None,
            "service": None,
            "ip": None,
            "cidr": None,
            "hostname": None,
            "port": None,
            "city": None,
            "state": None,
            "country": None,
            "asn": None,
            "header": None,
            "keywords": None,
            "desc": None,
            "title": None,
            "site": None,
        },
    },
}

# 系统默认的命令
cmd_dict = {
    "switch_control": switch_control,
    "stratagy": stratagy,
    "stratagymail": stratagymail,
    "stratagyscout": stratagyscout,
    "stratagyscan": stratagyscan,
}
