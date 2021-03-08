"""
管理iscan的下载插件，
关联的是scandownloader
决定每次下载的插件是谁
create by swm 2019/06/28
"""
import time
import traceback

from commonbaby.mslog import MsLogger, MsLogManager

from datacontract import IscanTask, EScanType
from idownclient.scan import Shodan, ScanTools


class ScanPlugManager(object):
    def __init__(self):
        # self._scan_threads_locker = threading.Lock()
        # self._scan_dealing_dict = {}
        self._logger: MsLogger = MsLogManager.get_logger("TaskManager")

    def iscandownload(self, task: IscanTask):
        try:

            if task.scantype == EScanType.ScanSearch:
                self._scan_shodan(task)
            elif task.scantype == EScanType.Scan:
                self._scan(task)
            else:
                self._logger.error(
                    f"Unknown scantype: {task.taskid} scantype:{task.scantype}\n{traceback.format_exc()}"
                )

        except Exception:
            self._logger.error(
                f"Deal scan task error, taskid: {task.taskid} scantype:{task.scantype}\n{traceback.format_exc()}"
            )

    def _scan_shodan(self, task: IscanTask):
        try:
            # with self._scan_threads_locker:
            #     if self._scan_dealing_dict.__contains__(task):
            #         self._logger.error(f'{task.taskid} is downloading')
            # zoomeye = ZoomEye(task)
            shodan = Shodan(task)
            # 因为ip存在的限制所以不适用多线程
            # thread1 = threading.Thread(target=self.exec_scaner, daemon=True, args=(zoomeye,))
            # thread2 = threading.Thread(target=self.exec_scaner, daemon=True, args=(shodan,))
            # thread1.start()
            # thread2.start()
            # with self._scan_threads_locker:
            #     self._scan_dealing_dict[task] = task.taskid
            # thread1.join()
            try:
                if shodan.download_data():
                    self._logger.info(
                        f"Iscan task {shodan.task.taskid} execute complete, misson accomplished."
                    )
                else:
                    self._logger.info(
                        f"Isacn task {shodan.task.taskid} execute failed, misson accomplished."
                    )
            except Exception:
                self._logger.error(
                    f"Execute iscantask error, error:{traceback.format_exc()}"
                )
            finally:
                # 当前任务的完成dict，这个等一秒是等待状态的回执
                time.sleep(1)
                if shodan.task is not None:
                    if callable(shodan.task.on_complete):
                        shodan.task.on_complete(shodan.task)
                # 这种用到才实例化的手动析构下
                del shodan
        except:
            self._logger.error(
                f"Scan search task error, taskid: {task.taskid} scantype:{task.scantype}\n{traceback.format_exc()}"
            )

    def _scan(self, task: IscanTask):
        timestart = int(time.time())
        try:
            sc = ScanTools(task)
            try:
                if sc.download_data():
                    self._logger.info(
                        f"Scan task {task.taskid} execute complete, misson accomplished."
                    )
                else:
                    self._logger.info(
                        f"Sacn task {task.taskid} execute failed, misson accomplished."
                    )
            except:
                self._logger.error(
                    f"Execute Scantools  error, error:{traceback.format_exc()}"
                )
            finally:
                # 当前任务的完成dict，这个等一秒是等待状态的回执
                time.sleep(1)
                if sc.task is not None:
                    if callable(sc.task.on_complete):
                        sc.task.on_complete(sc.task)
                # 这种用到才实例化的手动析构下
                del sc
                timestop = int(time.time())
                self._logger.info(
                    f"The Task start at {timestart}\nThe Task end at {timestop}\nA total of time consuming:{timestop-timestart}s"
                )
                with open("./scan_rate_test_result.txt", "a", encoding="utf-8") as fp:
                    fp.write(
                        f"Task:{task.taskid}\nstart at {timestart}\nend at {timestop}\nA total of time consuming:{timestop-timestart}s\n"
                    )
        except Exception:
            self._logger.error(
                f"Scan task error, taskid: {task.taskid} scantype:{task.scantype}\n{traceback.format_exc()}"
            )

    # def exec_scaner(self, ze: Shodan):
    #     """
    #     执行zoomeye的下载
    #     :param ze:
    #     :return:
    #     """
    #     try:
    #         if ze.download_data():
    #             self._logger.info(f"Iscan task {ze.task.taskid} execute complete, misson accomplished.")
    #         else:
    #             self._logger.info(f"Isacn task {ze.task.taskid} execute failed, misson accomplished.")
    #     except Exception:
    #         self._logger.error(f"Execute iscantask error, error:{traceback.format_exc()}")
    #     finally:
    #         # 当前任务的完成dict，这个等一秒是等待状态的回执
    #         time.sleep(1)
    #         if ze.task is not None:
    #             if callable(ze.task.on_complete):
    #                 ze.task.on_complete(ze.task)
    #         # 这种用到才实例化的手动析构下
    #         del ze
    #     return
