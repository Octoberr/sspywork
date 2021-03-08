"""
购物app的集合
"""
from .appbase import EAppClassify, AppConfig
from idownclient.spider import spidershopping

Shopping_apps = {
    # 购物网站类
    5001: AppConfig(
        appname="美团",
        apphosts=["www.meituan.com"],
        apptype=5001,
        appclassify=EAppClassify.Shopping,
        appclass=spidershopping.SpiderMeiTuan,
    ),
    5002: AppConfig(
        appname="亚马逊",
        apphosts=["www.amazon.com"],
        apptype=5002,
        appclassify=EAppClassify.Shopping,
        appclass=spidershopping.SpiderAmazon,
    ),
    5003: AppConfig(
        appname="苏宁易购",
        apphosts=["www.suning.com"],
        apptype=5003,
        appclassify=EAppClassify.Shopping,
        appclass=spidershopping.SpiderSuning,
    ),
    5004: AppConfig(
        appname="淘宝网",
        apphosts=["www.taobao.com"],
        apptype=5004,
        appclassify=EAppClassify.Shopping,
        appclass=spidershopping.SpiderTaoBao,
    ),
    5005: AppConfig(
        appname="京东",
        apphosts=["www.jd.com"],
        apptype=5005,
        appclassify=EAppClassify.Shopping,
        appclass=spidershopping.SpiderJingDong,
    ),
    5006: AppConfig(
        appname="唯品会",
        apphosts=["www.vip.com"],
        apptype=5006,
        appclassify=EAppClassify.Shopping,
        appclass=spidershopping.SpiderWeiPinhui,
    ),
    5007: AppConfig(
        appname="蘑菇街",
        apphosts=["www.mogujie.com"],
        apptype=5007,
        appclassify=EAppClassify.Shopping,
        appclass=spidershopping.SpiderMogujie,
    ),
    5008: AppConfig(
        appname="当当网",
        apphosts=["www.dangdang.com", "book.dangdang.com"],
        apptype=5008,
        appclassify=EAppClassify.Shopping,
        appclass=spidershopping.SpiderDangDang,
    ),
}
