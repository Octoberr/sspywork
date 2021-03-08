"""
重构telegram
并新增边写边读sqlite的功能
create by judy 20200518
"""
import base64
import os
import random
import re
import sqlite3
import subprocess
import sys
import time
import traceback
from pathlib import Path
from datetime import datetime
import pytz

from datacontract.outputdata import OutputData
from datacontract.idowndataset import Task
from datacontract.outputdata import OutputData
from idownclient.clientdatafeedback import EResourceType
from idownclient.config_spiders import telegramconfig
from idownclient.spider.appcfg import AppCfg
from ..spidersocialbase import SpiderSocialBase


class TelegramBase(SpiderSocialBase):
    def __init__(self, tsk: Task, appcfg: AppCfg, clientid):
        SpiderSocialBase.__init__(self, tsk, appcfg, clientid)
        self.telegram: Path = telegramconfig.telegram
        self._environment = True
        if not self.telegram.exists():
            self._logger.error("No telegram.jar in {}".format(telegramconfig.telegram))
            self._environment = False

        self.java: Path = telegramconfig.javapath
        if not self.java.exists():
            self._logger.error("No java in {}".format(telegramconfig.javapath))
            self._environment = False

        self.accountsdir = telegramconfig.accountsdata

        if self.task.globaltelcode is None or self.task.globaltelcode == "":
            self.task.globaltelcode = "+86"
        self._sectimeout: float = telegramconfig.timesec
        self._result = False
        self._stopsigin = False
        # self._userid = self.task.phone
        self._downloadprogress = re.compile(r"\d{1,3}\.\d{1,2}")
        # 0图片
        self.datatype = {
            EResourceType.Picture: [
                "bmp",
                "jpg",
                "png",
                "gif",
                "webp",
                "cr2",
                "tif",
                "jxr",
                "psd",
                "ico",
            ],
            EResourceType.Video: [
                "mp4",
                "avi",
                "mkv",
                "qlv",
                "m4v",
                "webm",
                "mov",
                "wmv",
                "mpg",
                "flv",
            ],
            EResourceType.Audio: [
                "mp3",
                "cd",
                "wave",
                "mid",
                "m4a",
                "ogg",
                "flac",
                "wav",
                "amr",
            ],
        }

    def _read_err_log(self, p: subprocess.Popen):
        if p is None or not isinstance(p, subprocess.Popen):
            raise Exception(
                "subprocess.Popen object is None while dealing the stdout stream"
            )
        while True:
            if self._stopsigin:
                break
            line = p.stderr.readline()
            if line is not None and line != "":
                self._logger.error(line)
            if p is None or p.returncode is not None:
                break

    def _std_flush(self, p: subprocess.Popen):
        """flush the standard stream"""
        while True:
            if self._stopsigin:
                break
            try:
                p.stdout.flush()
                p.stderr.flush()
                sys.stderr.flush()
                sys.stdout.flush()
            except:
                self._logger.warn(
                    f"Flush standard stream error: \nex:{traceback.format_exc()}"
                )
            finally:
                time.sleep(1)

    def _common_args(self, account) -> list:
        """get the common args for calling the telegram.
        including: -account -target -phone"""
        _account = account  # 登陆账号
        # target = tsk._fields["datadir"]  #已登陆账号文件存储目录
        # 暂时不使用传过来的账号存储路径，直接使用本地管理的账号路径
        _target = self.accountsdir
        randomsel = random.SystemRandom()
        phone = ["HUAWEIMate10", "Xiaomi6", "SamSungGALAXYNote8", "vivox20", "OPPOR11"]
        _phone = randomsel.choice(phone)  # 设备类型
        # _phone = 'Honor9'

        res = [
            f"-account {self.task.globaltelcode + _account}",
            f"-target {_target}",
            f"-phone {_phone}",
        ]
        return res

    def _run_telegram(
        self,
        *args,
        cmdtype: str,
        sudo: bool = False,
        rootDir: str = "./",
        taskid: str,
        stdout=None,
        stderr=None,
    ) -> subprocess.Popen:
        """wrapper of execute the telegram jar,
        auto find the target tasktype by self._tasktype.
        the sub-classes should only pass the special params"""
        if args is None:
            args = []

        # combine the stable params
        argnew = [
            f"-Dfile.encoding=UTF-8",
            f"-jar {self.telegram}",
            f"-{cmdtype}",
        ]
        argnew.extend(args)

        # execute
        p = self._run_process(
            str(self.java),
            *argnew,
            sudo=sudo,
            rootDir=rootDir,
            taskid=taskid,
            stdout=stdout,
            stderr=stderr,
        )
        return p

    def _run_process(
        self,
        executable: str,
        *args,
        sudo: bool = False,
        rootDir: str = "./",
        taskid: str = None,
        stdout=None,
        stderr=None,
    ) -> subprocess.Popen:
        """run process under current operation system and return the process object.
        executable: the executable binary path.
        arg: all args in a str.
        sudo: True if sudo
        rootDir: current work dir."""
        try:
            if not os.path.exists(rootDir):
                os.makedirs(rootDir)

            cmd = ""
            if sudo and not sys.platform.startswith("win32"):
                cmd = "sudo "
            params = " ".join(args)
            params = f"{executable} {params}"
            cmd = cmd + params

            # print cmd
            logmsg = cmd
            if taskid is not None and taskid != "":
                logmsg = f"{logmsg}"
            self._logger.info(logmsg)
            if (
                sys.platform.startswith("freebsd")
                or sys.platform.startswith("linux")
                or sys.platform.startswith("darwin")
            ):
                p = subprocess.Popen(
                    cmd,
                    shell=True,
                    cwd=rootDir,
                    bufsize=100000,
                    stdin=subprocess.PIPE,
                    stdout=stdout.fileno() if not stdout is None else subprocess.PIPE,
                    stderr=stderr.fileno() if not stderr is None else subprocess.PIPE,
                    close_fds=False,
                    universal_newlines=True,
                )
            else:
                p = subprocess.Popen(
                    cmd,
                    cwd=rootDir,
                    shell=False,
                    bufsize=10000,
                    stdin=subprocess.PIPE,
                    # open(fiout, 'w'),  # subprocess.PIPE,
                    stdout=stdout.fileno() if not stdout is None else subprocess.PIPE,
                    # open(fierr, 'w'),  # subprocess.PIPE,
                    stderr=stderr.fileno() if not stderr is None else subprocess.PIPE,
                    universal_newlines=True,
                    close_fds=False,
                )
            return p
        except Exception as ex:
            raise ex

    def _output_format_str(self, line_data):
        if line_data is None or line_data == b"":
            return ""
        if isinstance(line_data, str):
            return line_data
        elif isinstance(line_data, bytes):
            try:
                return line_data.decode("utf-8")
            except:
                return f"=?utf-8?b?{base64.b64encode(line_data).decode('utf-8')}"
        else:
            return repr(line_data)

    def _dict_factory(self, cursor, row):
        """
        格式化查询结果为字典
        :param cursor:
        :param row:
        :return:
        """
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def _text_factory(self, x):
        """text factory"""
        if x is None or x == "":
            return ""
        try:
            if isinstance(x, bytes):
                return x
            else:
                return repr(x)
        except Exception:
            return ""

    def _select_data(self, sqlpath, sql, pars):
        conn = sqlite3.connect(sqlpath)
        conn.row_factory = self._dict_factory
        conn.text_factory = self._text_factory
        c = conn.cursor()
        c.execute(sql, pars)
        res = c.fetchall()
        conn.close()
        return res

    def delete_complete_file(self, succ: bool, data: OutputData):
        """
        回调函数，在文件被读完后删除
        :param filename:
        :return:
        """
        res = True
        try:
            if not hasattr(data, "isdeleteable") or not hasattr(
                data, "filepath_telegram"
            ):
                return res
            if not data.isdeleteable:
                return res
            if data.filepath_telegram is None:
                self._logger.error("Telegram deleteable filepath is None")
                return res

            stm = data.get_stream()
            if stm is not None and not stm.closed:
                stm.close()
            if not data.filepath_telegram.exists():
                self._logger.error(
                    "Telegram deletable file is not found: {}".format(
                        data.filepath_telegram
                    )
                )
                return res

            data.filepath_telegram.unlink()
            # filename.unlink()
        except:
            res = False
        return res

    def mvsqlitetobak(self, dbpath: str):
        """
        备份下载的数据库，但是数据库好像是有持续下载的功能
        所以这个方法目前弃用了
        整理by judy 2020/05/18
        :param dbpath:
        :return:
        """
        sqldbpath = Path(dbpath)
        dbdir = sqldbpath.parent
        # 备份文件夹
        bakdir = dbdir / "dbbak"
        # 检查文件夹是否创建，没有创建则创建
        bakdir.mkdir(exist_ok=True)
        bakpath = bakdir / (
            str(int(datetime.now(pytz.timezone("Asia/Shanghai")).timestamp() * 1000))
            + ".sqlite"
        )
        sqldbpath.replace(bakpath)
        return

    # def _try_decode(self, s: bytes, charset: str):
    #     try:
    #         if charset is None or charset == "":
    #             raise ValueError("charset is empty")
    #
    #         if s is None:
    #             return ''
    #
    #         return s.decode(charset)
    #
    #     except Exception:
    #         return None