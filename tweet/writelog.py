"""
传入字符串编写log,暂时以日期创建log文件
createby swm
2018/06/13
"""
import datetime
import logging
from conf import config
# from pathlib import Path
#
# # 当前文件夹
# file = Path(__file__).parent
# logfile = file/Path('../log')


class WRITELOG:

    def __init__(self):
        self.logpath = config['logpath']

    def createlogfile(self):
        today = datetime.datetime.today()
        name = datetime.datetime.strftime(today, "%Y%m%d")
        filepath = self.logpath/'{}.log'.format(name)
        return filepath

    def writelog(self, strlog):
        logfile = self.createlogfile()
        logging.basicConfig(filename=logfile, filemode='a', level=logging.INFO)
        logging.info('{}-{}'.format(datetime.datetime.now(), strlog))
        return
