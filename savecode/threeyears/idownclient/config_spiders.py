"""
config for spiders
爬虫插件的配置
这里主要放一些程序中的配置
集中写了比较方便改
create by judy 2020/08/20
"""

import os

from idownclient.spider.spidersocial.spidertelegram.telegramconfig import TelegramConfig

# douyin config
douyinip = "127.0.0.1"
douyinport = 9527
# zoomeye
zoomeyeconf = {"username": "sldjlv@qq.com", "password": "Nmsb123456"}

# idown的telegram路径配置
telegramconfig = TelegramConfig(
    accountsdata=None,
    # javapath=r'D:\judydata\telegramwrapper\telegram\java',
    javapath=None,
    # telegram=r'D:\judydata\telegramwrapper\telegram\telegram.jar',
    telegram=None,
    timesex=None,
)

# shodan
shodanconf = {
    "apikey": "rfGs6zPuNnF8UaHWRB0NrwrEqCPOhIJK",
    "get_all_data_switch": False,
    "error_times": 15,
}

# 特定目标侦查
# 可同时处理scouter的线程，默认为10个
# controler,这个玩意以前有3级查询，
# 可能一个任务会产生上万个任务，所以需要开多线程，但是现在不需要了by judy 2020/09/04
scouterconf = {"scouter_threads": 10, "controler_thread_num": 1}

webdriver_path_debian: str = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "resource/webdriver/chromedriver",
    )
)
webdriver_path_win: str = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "resource/webdriver/chromedriver.exe",
    )
)

# 搜索引擎取结果，默认为一页，一页10条
searchconfig = {"reslimit": 10}

# telegram_pre_count，这个账号为我方账号，有登陆凭证可以使用
telegramaccount = {"phone": "+8618161224132"}
bingapikey = {"key": "fd8510df76b542c29b99645abfbfd33d"}

# dbip库每月更新链接，重新购买后需要更新这个配置
dbip_upgrade_url = "https://db-ip.com/account/7fcd7421494b209426e44b8729aa1606c973e49a/db/ip-to-location-isp/"

# 是否打印扫描日志，自己进行大规模扫描是不需要日志的, 默认为True，资产扫描模式下为False
iscan_log = False