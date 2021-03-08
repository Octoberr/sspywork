"""配置数据标准转换"""

# -*- coding:utf-8 -*-

import uuid

from datacontract import ETaskType

from .stdconvertmanagement import (
    ConvertConfig, ConverterBcp, ConverterCmd, ConverterCookie, ConverterField,
    ConverterIScanTask, ConverterTask, ConverterIScoutTask)


def uuid1_():
    """用于生成GUID"""
    return str(uuid.uuid1())


stdconvertconfig = ConvertConfig(
    dicconverters={
        "iscouttaskconverter":
        ConverterIScoutTask(
            uniquename="iscouttaskconverter",
            extensions=[".iscout_task"],
            fields={
                "createtime": ConverterField(key='createtime'),
                "taskid": ConverterField(key='taskid'),
                "batchid": ConverterField(key='batchid'),
                "source": ConverterField(key='source', required=False),
                "objecttype": ConverterField(key='objecttype'),
                "object": ConverterField(key='object'),
                "cmdid": ConverterField(key='scantype', required=False),
                "cmd": ConverterField(key='scantype', required=False),
            },
            extendfields=None),
        "iscantaskconverter":
        ConverterIScanTask(
            uniquename="iscantaskconverter",
            extensions=[".iscan_task"],
            fields={
                "createtime": ConverterField(key='createtime'),
                "taskid": ConverterField(key='taskid'),
                "source": ConverterField(key='source', required=False),
                "scantype": ConverterField(key='scantype'),
                "cmdid": ConverterField(key='scantype', required=False),
                "cmd": ConverterField(key='scantype', required=False),
            },
            extendfields=None),
        "cmdconverter":
        ConverterCmd(
            uniquename="cmdconverter",
            extensions=[".idown_cmd"],
            fields={
                "cmdid": ConverterField(key='cmdid'),
                "cmd": ConverterField(key='cmd'),
                "source": ConverterField(key='source', required=False),
            },
            extendfields=None),
        "taskconverter":
        ConverterTask(
            uniquename="taskconverter",
            extensions=[".idown_task"],
            fields={
                "taskid":
                ConverterField(key='taskid'),
                "parenttaskid":
                ConverterField(key='parenttaskid', required=False),
                "batchid":
                ConverterField(key='batchid'),
                "parentbatchid":
                ConverterField(key='parentbatchid', required=False),
                "tokenid":
                ConverterField(key='tokenid'),
                "tasktype":
                ConverterField(key='tasktype'),
                "apptype":
                ConverterField(key='apptype', required=False),
                "forcedownload":
                ConverterField(key='forcedownload', required=False),
                "globaltelcode":
                ConverterField(key='globaltelcode', required=False),
                "phone":
                ConverterField(key='phone', required=False),
                "account":
                ConverterField(key='account', required=False),
                "password":
                ConverterField(key='password', required=False),
                "input":
                ConverterField(key='input', required=False),
                "source":
                ConverterField(key='source', required=False),
                "cmdid":
                ConverterField(key='cmdid', required=False),
                "cmd":
                ConverterField(key='cmd', required=False)
            },
            extendfields=None),
        "cookieconverter":
        ConverterCookie(
            uniquename="cookieconverter",
            extensions=[".an_cookie"],
            fields={
                "time": ConverterField("time", True),
                "account": ConverterField("account", False),
                "password": ConverterField("password", False),
                "host": ConverterField("host", False),
                "url": ConverterField("url", False),
                "cookie": ConverterField("cookie", False),
            },
            extendfields={
                "taskid": uuid1_,
                "batchid": uuid1_,
                "tokenid": uuid1_,
                "tasktype": ETaskType.LoginDownload.value,
            }),
        "bcpconverter":
        ConverterBcp(
            uniquename="bcpconverter",
            extensions=[".zip"],
            fields={
                "url": ConverterField("url"),
                "cookie": ConverterField("cookie"),
            },
            extendfields={
                "taskid": uuid1_,
                "batchid": uuid1_,
                "tokenid": uuid1_,
                "tasktype": ETaskType.LoginDownload.value,
                # 这里来的bcp一定是国内手机，有国外手机再说
                "globaltelcode": "+86",
            })
    })
