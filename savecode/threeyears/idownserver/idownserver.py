"""server"""

# -*- coding:utf-8 -*-

import json
import os
import queue
import shutil
import threading
import time
import traceback
import uuid

from commonbaby.helpers import helper_file, helper_str
from commonbaby.mslog import MsLogger, MsLogManager

from datacontract import ALL_APPS, AppConfig
from inputmanagement.inputmanagement import InputData, InputManagement
from outputmanagement import OutputManagement

from .config_input import inputconfig
from .config_output import outputconfig, outputdir, tmpdir
from .config_outputstandard import stdconfig
from .servicemanager.servicemanager import ServiceManager

VERSION = '1.1.3'
DATE = '2020.11.25'


class IDownServer:
    """idown server"""
    def __init__(self):
        self._logger: MsLogger = MsLogManager.get_logger("idownserver")
        OutputManagement.static_initial(outputconfig, stdconfig)
        self._inputmanagement = InputManagement(inputconfig, self.on_data_in)
        self._servicemanager = ServiceManager()

        # 隔段时间就生成一次dicapp（dicapp后面可能会是动态的，因为采集端可能掉线，崩掉等）
        self._t_dicapp = threading.Thread(target=self._generate_dicapp,
                                          name='gen_dicapp',
                                          daemon=True)

    def start(self):
        """start deal"""
        if not self._t_dicapp._started._flag:
            self._t_dicapp.start()
        self._inputmanagement.start()
        self._servicemanager.start()

    def on_data_in(self, data: InputData):
        """new data in"""
        try:
            if data is None:
                self._logger.error("Input data is None")
                data.on_complete(True)
                return

            self._servicemanager.on_data_in(data)

        except Exception:
            self._logger.error("Deal error:\ndata:%s\nex:%s" %
                               (data._source, traceback.format_exc()))
            data.on_complete(False)

    def _generate_dicapp(self):
        """output the app dictionary.
        程序启动时需要把当前idown支持的app列表返回"""
        if not isinstance(ALL_APPS, dict) or len(ALL_APPS) < 1:
            raise Exception("Datacontract.ALL_APPS is invalid")

        while True:
            try:
                self._gen_dicapp()

                # 暂定为只有启动时生成
                # 后面要改为只要变动就生成
                break
            except Exception:
                self._logger.error("Generate dicapp error: {}".format(
                    traceback.format_exc()))
            finally:
                # 暂定10分钟输出一次，后面dicapp动态了再调整
                time.sleep(10 * 60)

    def _gen_dicapp(self):
        if not os.path.exists(tmpdir):
            os.makedirs(tmpdir)
        tmpfidicapp = os.path.join(
            tmpdir, "{}.idown_dic_app".format(str(uuid.uuid1())))
        while os.path.exists(tmpfidicapp):
            tmpfidicapp = os.path.join(
                tmpdir, "{}.idown_dic_app".format(str(uuid.uuid1())))

        with open(tmpfidicapp, mode='a', encoding='utf-8') as fs:
            for app in ALL_APPS.values():
                app: AppConfig = app
                fs.write('appname:{}\n'.format(
                    helper_str.base64format(app._appanme)))
                fs.write('apptype:{}\n'.format(app._apptype))
                fs.write('appclassify:{}\n'.format(app._appclassify.value))
                fs.write('requirepreaccount:{}\n'.format(
                    str(int(app._requirepreaccount))))
                fs.write('requirecrosswall:{}\n'.format(
                    str(int(app._crosswall))))
                fs.write('enable:{}\n'.format(str(int(app._enable))))
                fs.write('remark:{}\n'.format(
                    helper_str.base64format(json.dumps(app._apphosts))))
                fs.write('\n')

        if not os.path.exists(outputdir):
            os.makedirs(outputdir)
        outfidicapp = os.path.join(
            outputdir, "{}.idown_dic_app".format(str(uuid.uuid1())))
        while os.path.exists(outfidicapp):
            outfidicapp = os.path.join(
                outputdir, "{}.idown_dic_app".format(str(uuid.uuid1())))
        shutil.move(tmpfidicapp, outfidicapp)
