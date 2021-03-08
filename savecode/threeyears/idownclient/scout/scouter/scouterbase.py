"""
scouter base
新增任务停止功能
"""
import traceback
from abc import abstractmethod

from commonbaby.httpaccess import HttpAccess
from commonbaby.mslog import MsLogger, MsLogManager

from datacontract import IscoutTask, PrglogBase
from idownclient.clientdbmanager import DbManager
from idownclient.config_detectiontools import dtools
from idownclient.config_task import clienttaskconfig
from jsonoutputer import Outputjtf
from ...clientdatafeedback.scoutdatafeedback.scoutfeedbackbase import ScoutFeedBackBase


class ScouterBase(object):
    """Scouter base class"""

    def __init__(self, task: IscoutTask):
        self.task = task
        self.tmppath = clienttaskconfig.tmppath
        self.outpath = clienttaskconfig.outputpath
        self._ha = HttpAccess()
        # 插件名字
        self._name = type(self).__name__
        self._logger: MsLogger = MsLogManager.get_logger(f"{self._name}_{self.task.taskid}")
        self._sqlfunc = DbManager

        # 最大的输出条数
        self.max_output = 10000
        # 新增reason字段，需要对应打击武器的
        self.dtools = dtools
        # 新增数据统计，modify by judy 2020/08/10
        self.output_count = 0
        # 日志log后缀，create by judy 2020/08/12
        self._log_suffix = 'prg_log'

    def outputdata(self, resdata: dict, suffix):
        """
        输出字典，json结果
        """
        if suffix != self._log_suffix:
            self.output_count += 1
        try:
            outname = Outputjtf.output_json_to_file(resdata, self.tmppath, self.outpath, suffix)
            self._logger.info(f'Output a data success, filename:{outname}')
        except:
            self._logger.error(
                f"Output json data error, err:{traceback.format_exc()}")
        return

    def _outprglog(self, log):
        """
        新增日志输出功能，modify by judy 2020/08/10
        """

        log = PrglogBase('IdownClient', '1.0', log, self.task)
        self.outputdata(log.output_dict(), self._log_suffix)
        return

    def scout(self, level: int, obj: ScoutFeedBackBase) -> iter:
        """level: recursion level\n
           obj: target object"""
        try:

            for result in self._scout(level, obj):
                yield result
                # retry
            # 下载结束，单个任务需要给回馈
        except:
            # 下载失败
            self._logger.error(
                f"Scouter Download error, err:{traceback.format_exc()}")

    def _scout(self, level, obj: ScoutFeedBackBase) -> iter:
        """控制哪些数据输出，哪些数据需要yield回去"""
        try:
            for data in self._scoutsub(level, obj):

                # 可作为根节点的数据对象才返回回去
                if not isinstance(data, ScoutFeedBackBase):
                    continue

                yield data

        except Exception:
            self._logger.error("Scout sub error: {}".format(
                traceback.format_exc()))

    @abstractmethod
    def _scoutsub(self, level: int, obj: ScoutFeedBackBase) -> iter:
        """子类自行实现据体业务"""
        raise NotImplementedError()

    def __del__(self):
        self._logger.debug("Scouter download complete.")
