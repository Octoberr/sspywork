"""
旅行订单
"""
from .appbase import EAppClassify, AppConfig
from idownclient.spider import spidertravel

Travel_apps = {
    # 行程类
    4001:
        AppConfig(
            appname='去哪儿网',
            apphosts=["www.qunar.com"],
            apptype=4001,
            appclassify=EAppClassify.Travel,
            appclass=spidertravel.SpiderQunar),
    4002:
        AppConfig(
            appname='百程旅游',
            apphosts=["www.baicheng.com"],
            apptype=4002,
            appclassify=EAppClassify.Travel,
            appclass=spidertravel.SpiderBaicheng),
    4003:
        AppConfig(
            appname='百度旅游',
            apphosts=["lvyou.baidu.com"],
            apptype=4003,
            appclassify=EAppClassify.Travel,
            appclass=spidertravel.SpiderBaidu),
    4004:
        AppConfig(
            appname='海南航空',
            apphosts=["www.hnair.com"],
            apptype=4004,
            appclassify=EAppClassify.Travel,
            appclass=spidertravel.SpiderHainanAir),
    4005:
        AppConfig(
            appname='凯撒旅游',
            apphosts=["www.caissa.com.cn"],
            apptype=4005,
            appclassify=EAppClassify.Travel,
            appclass=spidertravel.SpiderCaisa),
    4006:
        AppConfig(
            appname='穷游网',
            apphosts=["www.qyer.com"],
            apptype=4006,
            appclassify=EAppClassify.Travel,
            appclass=spidertravel.SpiderQyer),
    4007:
        AppConfig(
            appname='途牛网',
            apphosts=["www.tuniu.com"],
            apptype=4007,
            appclassify=EAppClassify.Travel,
            appclass=spidertravel.SpiderTuniu),
    4008:
        AppConfig(
            appname='携程网',
            apphosts=["www.ctrip.com"],
            apptype=4008,
            appclassify=EAppClassify.Travel,
            appclass=spidertravel.SpiderCtrip),
    4009:
        AppConfig(
            appname='南方航空',
            apphosts=["www.csair.com"],
            apptype=4009,
            appclassify=EAppClassify.Travel,
            appclass=spidertravel.SpiderCsair),
    4010:
        AppConfig(
            appname='艺龙',
            apphosts=["www.elong.com"],
            apptype=4010,
            appclassify=EAppClassify.Travel,
            appclass=spidertravel.SpiderElong),
    # 4011:
    #     AppConfig(
    #         appname='深圳航空',
    #         apphosts=["www.shenzhenair.com"],
    #         apptype=4011,
    #         appclassify=EAppClassify.Travel,
    #         appclass=spidertravel.SpiderShenzhenAir),
    4012:
        AppConfig(
            appname='速8酒店',
            apphosts=["www.super8.com.cn"],
            apptype=4012,
            appclassify=EAppClassify.Travel,
            appclass=spidertravel.SpiderSuper8),
    4013:
        AppConfig(
            appname='东方航空',
            apphosts=["www.ceair.com"],
            apptype=4013,
            appclassify=EAppClassify.Travel,
            appclass=spidertravel.SpiderCeair),
    4014:
        AppConfig(
            appname='春秋航空',
            apphosts=["www.ch.com"],
            apptype=4014,
            appclassify=EAppClassify.Travel,
            appclass=spidertravel.SpiderChair),
    4015:
        AppConfig(
            appname='同程',
            apphosts=["www.ly.com"],
            apptype=4014,
            appclassify=EAppClassify.Travel,
            appclass=spidertravel.SpiderTongCheng),
    4016:
        AppConfig(
            appname='途家',
            apphosts=["www.tujia.com"],
            apptype=4016,
            appclassify=EAppClassify.Travel,
            appclass=spidertravel.SpiderTujia),
    4017:
        AppConfig(
            appname='马蜂窝',
            apphosts=["www.mafengwo.cn"],
            apptype=4017,
            appclassify=EAppClassify.Travel,
            appclass=spidertravel.SpiderMafengwo),
}
