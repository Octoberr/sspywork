"""
网约车，共享单车等
"""
from .appbase import EAppClassify, AppConfig
from idownclient.spider import spidertaxi

Taxi_apps = {
    # 出行，网约车，共享车，租车类
    2001:
        AppConfig(
            appname='ofo小黄车',
            apphosts=["ofo.com"],
            apptype=2001,
            appclassify=EAppClassify.Taxi,
            appclass=spidertaxi.SpiderOfo),
    2002:
        AppConfig(
            appname='uber',
            apphosts=["uber.com"],
            apptype=2002,
            appclassify=EAppClassify.Taxi,
            appclass=spidertaxi.SpiderUber),
}
