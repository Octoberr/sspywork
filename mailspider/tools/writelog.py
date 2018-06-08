"""
传入字符串编写log,暂时以日期创建log文件
createby swm
2018/06/06
"""
import datetime
import logging

from pathlib import Path

# 当前文件夹
file = Path(__file__).parent
logfile = file/Path('../log')


class WRITELOG:

    def createlogfile(self):
        today = datetime.datetime.today()
        name = datetime.datetime.strftime(today, "%Y%m%d")
        filepath = logfile/'{}.log'.format(name)
        return filepath

    def writelog(self, strlog):
        logfile = self.createlogfile()
        logging.basicConfig(filename=logfile, filemode='a', level=logging.INFO)
        logging.info('{}-{}'.format(datetime.datetime.now(), strlog))
        return
