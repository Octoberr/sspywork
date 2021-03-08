"""dealer config"""

# -*- coding:utf-8 -*-

from datacontract import (
    ExtMatcher,
    StatusBasic,
    StatusTask,
    StatusTaskInfo,
    Task,
    TaskBack,
)
from idownclient.clientdatafeedback import (
    CONTACT,
    EML,
    ICHATGROUP,
    ICHATLOG,
    INETDISKFILE,
    INETDISKFILELIST,
    ISHOPPING,
    ITRAVELORDER,
    ITRIP,
    PROFILE,
    RESOURCES,
    IdownLoginLog,
)

# from .dnsreq import DnsReqDealer
from .feedbackdealer import FeedbackDealer
from .servicemanager import DealerConfig
from .statusmantainer import StatusMantainer
from .taskbackdealer import TaskBackManager
from .taskdispatcher import TaskDispatchManager

dealerconfig = DealerConfig(
    dealers=[
        # DnsReqDealer(
        #     ExtMatcher(exts=[
        #         "an_dns",
        #         "an_dns_client",
        #     ])
        # ),
        # 各种令牌接收接口
        TaskDispatchManager(
            ExtMatcher(
                exts=[
                    "idown_task",  # 中心下发的任务
                    "idown_cmd",  # 中心下发的命令
                    "iscan_task",  # 扫描任务
                    "iscout_task",  # 侦察任务
                    "an_cookie",  # 前端还原的cookie
                    "zip",  # bcp格式的4g cookie
                ]
            )
        ),
        # 采集端运维状态维护
        # 采集端5分钟回一次信息，server那边如果10分钟没有更新则表示这台机器已经失活
        StatusMantainer(
            ExtMatcher(
                exts=[
                    "idown_status_basic",
                    "idown_status_task",
                    "idown_status_tasks",
                ]
            ),
            heartbeat=600000,
        ),
        # 测试将时间修改的很大，减少测试弯路
        # 各采集端回传的任务回馈信息解析、转换、调度、业务、合并处理
        TaskBackManager(
            ExtMatcher(
                exts=[
                    "idown_btask_back",
                    "idown_cmd_back",
                    "iscan_task_back",
                    "iscout_btask_back",
                    "iscout_task_back",
                    "automated_btask_back",
                ]
            )
        ),
        # 采集数据记录、处理、统计、回传
        FeedbackDealer(
            ExtMatcher(
                exts=[
                    # 主动下载
                    "idown_profile",
                    "idown_contact",
                    "idown_loginlog",
                    "idown_resource",
                    "eml",
                    "inetdisk_filelist",
                    "inetdisk_file",
                    "ichat_group",
                    "ichat_log",
                    "itrip_record",
                    "itravel_order",
                    "ishopping_order",
                    # 重点区域
                    "iscan",
                    "iscan_search",
                    "iscan_expdb",
                    "iscan_expdb_exp",
                    "iscan_expdb_app",
                    "iscan_expdb_screenshot",
                    "iscan_expdb_doc",
                    "geoname",
                    # 特定目标
                    "iscout_domain",  # 域名
                    "iscout_ip",  # IP
                    "iscout_url",  # URL
                    "iscout_email",  # 邮箱
                    "iscout_phone",  # 电话
                    "iscout_networkid",  # 网络id
                    "iscout_screenshot_url",  # URL侦察截屏数据
                    "iscout_screenshot_se",  # 搜索引擎截屏数据
                    "iscout_searchengine_file",  # 搜索引擎文件下载
                    "iscout_networkid_post",
                    "iscout_networkid_msg",
                    "iscout_networkid_profile",
                    "iscout_networkid_resource",
                    "client_log",  # idown日志文件
                    "user_status",  # 用户状态文件
                    # 程序日志
                    "prg_log",
                ]
            )
        ),
    ]
)
