"""配置数据输入"""

# -*- coding:utf-8 -*-

from inputmanagement.inputconfig import InputConfig
from inputmanagement.inputfile.inputfile import InputerFile

inputconfig = InputConfig(
    maxdealingqueuecount=1000,
    dicinputers={
        "zplus": InputerFile(
            uniqueName="zplus",
            inputdir=r"./_serverinput",
            platform="zplus",
            clasifiers={"resorucetype": "cookie"},
            maxDealingQueue=20,
            encoding="utf-8",
            succ_file_delete=False,
            succdir=r"./_serversucc",
            succfilekeepcount=-1,
            succfilekeepdays=-1,
            error_file_delete=False,
            errordir=r"./_servererror",
            errorfilekeepcount=-1,
            errorfilekeepdays=-1,
        ),
        "server_status": InputerFile(
            uniqueName="server_status",
            inputdir=r"./_serverstatus",
            platform="zplus",
            clasifiers=None,
            maxDealingQueue=20,
            encoding="utf-8",
            succ_file_delete=False,
            succdir=r"./_serversucc",
            succfilekeepcount=-1,
            succfilekeepdays=-1,
            error_file_delete=False,
            errordir=r"./_servererror",
            errorfilekeepcount=-1,
            errorfilekeepdays=-1,
        ),
        "zplan": InputerFile(
            uniqueName="zplan",
            inputdir=r"./_serverinput_zp",
            platform="zplan",
            clasifiers={"resorucetype": "cookie"},
            maxDealingQueue=20,
            encoding="utf-8",
            succ_file_delete=False,
            succdir=r"./_serversucc",
            succfilekeepcount=-1,
            succfilekeepdays=-1,
            error_file_delete=False,
            errordir=r"./_servererror",
            errorfilekeepcount=-1,
            errorfilekeepdays=-1,
        ),
    },
)
