"""
iscan 插件的基类
create by judy 2019/06/25
"""
import time
import traceback
from abc import abstractmethod
from datetime import datetime

import pytz
from commonbaby.mslog import MsLogger, MsLogManager

from datacontract import IscanTask, ECommandStatus, ETaskStatus, IdownCmd, PrglogBase
from idownclient.clientdbmanager import DbManager
from idownclient.config_spiders import iscan_log
from jsonoutputer import Outputjtf
from ..clientdbmanager.sqlcondition import ESqlComb, SqlCondition, SqlConditions
from ..config_task import clienttaskconfig
from ..iscanmanagement import ScanManageBase


class ScanPlugBase(object):
    def __init__(self, task: IscanTask):
        self.task = task
        self.suffix = "iscan_search"
        self.tmppath = clienttaskconfig.tmppath
        self.outpath = clienttaskconfig.outputpath
        # self._ha = HttpAccess()
        # 插件名字
        self._name = type(self).__name__

        self._logger: MsLogger = MsLogManager.get_logger(
            f"{self._name}_{self.task.taskid}"
        )

        self._sqlfunc = DbManager

        # 公用信息
        # 限制搜索条数
        self.count = 0
        self.count_limit = int(self.task.cmd.stratagyscan.search.count)
        # 查询的条数不能为0
        if self.count_limit == 0:
            raise Exception("Task count cant be None")

        # 新增暂停下载功能, 停止标志, 默认不停止, 1表示继续下载不停False, 0表示停止True
        self._stop_sign = False
        # 程序执行中
        self._running = True
        # 日志log后缀，create by judy 2020/08/12
        self._log_suffix = "prg_log"
        self.output_count = 0

    def _outputdata(self, resdata: dict, in_suffix=None, file_name=None):
        if not isinstance(resdata, dict):
            self._logger.error(f"Cant output {resdata}, please check the error")
            return
        try:
            # 这里应该是允许ascii字符的，因为网页本身是unicode的话不允许输出可能就会报错
            if in_suffix is not None:
                suffix = in_suffix
            else:
                suffix = self.suffix
            outname = Outputjtf.output_json_to_file(
                resdata,
                self.tmppath,
                self.outpath,
                suffix,
                ensure_ascii=True,
                file_name=file_name,
            )
            self._logger.info(f"Output a data success, filename:{outname}")
        except:
            self._logger.error(f"Output json data error, err:{traceback.format_exc()}")
        return

    def _write_iscantaskback(
        self, cmdstatus: ECommandStatus, scanrecvmsg, elapsed: float = None
    ):
        ScanManageBase.write_iscanback(
            self.task, cmdstatus, scanrecvmsg, elapsed=elapsed
        )
        return

    def _outprglog(self, log):
        """
        新增日志输出功能，modify by judy 2020/08/10
        """
        if iscan_log:
            log = PrglogBase("IdownClient", "1.0", log, self.task)
            self._outputdata(log.output_dict(), self._log_suffix)
        return

    def download_data(self):
        """
        base里面定义下载流程
        modify by judy 2020/06/03
        新增提前停止功能
        :return:
        """
        # 新加需求，输出统计，如果没有扫描到数据，那么提示未侦查到数据

        try:
            for data in self._download_data():
                self._outputdata(data)
            if self.output_count > 0:
                msg = "扫描完成，侦查到相关数据"
            else:
                msg = "扫描完成，未侦查到数据"
            # 增加任务的结束时间，add by judy 2019/11/18
            taskstoptime = datetime.now(pytz.timezone("Asia/Shanghai")).timestamp()
            elapsed = taskstoptime - self.task.taskstarttime
            if self._stop_sign:
                self._logger.info(
                    f"Scan stop in advance, periodnum:{self.task.periodnum}, {msg}"
                )
                self.task.taskstatus = ECommandStatus.Cancelled
            else:
                self._logger.info(
                    f"Scan downloading data complete, periodnum:{self.task.periodnum}, {msg}"
                )
                self.task.taskstatus = ECommandStatus.Succeed
            self._write_iscantaskback(self.task.taskstatus, msg, elapsed=elapsed)
            res = True
        except:
            self._logger.error(
                f"Downloading iscan data error, err:{traceback.format_exc()}"
            )
            self._write_iscantaskback(ECommandStatus.Failed, "扫描程序出错")
            res = False
        finally:
            # 下载完成后需要更新一些字段，目前没有说具体要更新哪些，也懒得去写扩展直接
            # 下载完成后需要更新一些字段的信息，目前这两个字段是用于循环下载，taskstatus
            # 等到实在是需要更新的字段多了，那么就在tbiscantask里增加一个方法，利用结束完成的task更新数据库的字段
            self._sqlfunc.update_iscan_status(
                "taskstatus", ETaskStatus.DownloadCompleted.value, self.task.taskid
            )
            self._sqlfunc.update_iscan_status(
                "sequence", self.task._sequence, self.task.taskid
            )
        return res

    @abstractmethod
    def _download_data(self) -> iter:
        """
        子类需要继承实现的下载流程
        :return:
        """
        return []

    def _get_stop_sign(self):
        """
        单个线程不断在数据库中查询停止标志
        改变停止的状态
        :return:
        """
        # sql = '''
        # SELECT cmdid, cmd FROM iscantask
        # LEFT OUTER JOIN idowncmd USING (cmdid)
        # WHERE taskid=?
        # '''
        # pars = (self.task.taskid, )
        while self._running:
            try:
                res = self._sqlfunc.query_iscan_task(
                    SqlConditions(
                        SqlCondition(
                            colname="taskid", val=self.task.taskid, comb=ESqlComb.And
                        ),
                    )
                )
                if len(res) == 0 or res[0].get("cmd") is None:
                    continue
                cmd = IdownCmd(res[0].get("cmd"))
                # 测试使用，到时候删除，by judy 2020/06/03
                self._logger.trace(f"Iscan get cmd, cmd:{cmd}")
                if (
                    cmd.switch_control is not None
                    and cmd.switch_control.download_switch is not None
                ):
                    self._stop_sign = int(cmd.switch_control.download_switch) == 0
            except:
                self._logger.error(
                    f"Something wrong when get stopsign,err:{traceback.format_exc()}"
                )
                continue
            finally:
                # 以防万一不要频繁的访问数据库,
                # 这个设置的时间可以等长一点，也许整个任务都不会有停止下载的设置
                time.sleep(2)
