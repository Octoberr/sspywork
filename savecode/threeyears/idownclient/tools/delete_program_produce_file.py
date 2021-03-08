"""
在python运行的过程中有时候会产生写莫名其妙的文件
可能是程序本身产生的，也可能是程序使用的一些工具产生的
先尝试删除看看，如果后续程序出现问题则停止这个程序
create by judy 2020/08/20
"""

import threading
import time
from pathlib import Path

from commonbaby.mslog import MsLogger, MsLogManager


class DPPF(object):
    def __init__(self):
        # 这些文件默认都生成在当前文件夹下
        self._current_path = Path(r'./')
        self._logger: MsLogger = MsLogManager.get_logger('DPPF')

    def _delete_ppf(self):
        """
        删除文件
        """
        while True:
            try:
                for fi in self._current_path.iterdir():
                    try:
                        finame = fi.name
                        if finame.startswith('core'):
                            fi.unlink()
                            self._logger.debug(f'Clean a ppf filename:{finame}')
                    except Exception as ee:
                        self._logger.debug(f'Cleaner one ppf file err: {ee}')

            except Exception as e:
                self._logger.debug(f'Cleaner err: {e}')
                time.sleep(1)
            finally:
                # 一小时检测一些
                time.sleep(360)
                self._logger.info(f'Cleaner will restart asfter {6} minutes')

    def start(self):
        """
        开启线程
        """
        thread1 = threading.Thread(target=self._delete_ppf,
                                   name="delete_program_produce_file")
        thread1.start()
