"""
Author: judy
Date: 2020-11-10 09:15:34
LastEditTime: 2020-11-10 09:15:39
LastEditors: your name
Description: In User Settings Edi
FilePath: \idown_new\idownclient\scout\plugin\telegram\telegrambase.py
telegram代码重构
1.允许用户登陆自己的手机账号和下载监控群消息
2.允许用户查询别的手机号是否在线
"""
import os
import base64
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import threading
import time
import traceback
import random
from idownclient.clientdatafeedback.scoutdatafeedback import EResourceType

from datacontract.iscoutdataset import IscoutTask
from ..scoutplugbase import ScoutPlugBase, MyThread


class TelegramBase(ScoutPlugBase):

    source = "Telegram"

    def __init__(self, task: IscoutTask):
        ScoutPlugBase.__init__(self)
        self.task = task
        # 目前做的东西都在resource里,这里面包含了java, jar, accounts data
        self._t_file = Path("./resource/telegramsource")
        # 判断下jar
        self._jar = self._t_file / "telegram.jar"
        if not self._jar.exists():
            # raise Exception('telegram.jar is not exists, please copy jar to telegramsource.')
            pass
        # 判断下java
        self._java_path = self._t_file / "jdk1.8.0_181"
        if not self._java_path.exists():
            # raise Exception('Java File is not exists, please copy java file to telegramsource.')
            pass
        # 判断完成后拿java的路径
        self._java = self._java_path / "bin/java"
        # 资源数据类型
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
            EResourceType.Audio: [
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
            EResourceType.Video: [
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
        # 默认gcode为中国电话+86,但是具体gcode由前端用户指定
        self._gcode = "+86"
        self._stopsigin = False
        self._downloadprogress = re.compile(r"\d{1,3}\.\d{1,2}")
        # 设置下默认超时时间 15分钟
        self._sectimeout = 15 * 60

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
                # print(line)
            if p is None or p.returncode is not None:
                break

    def _std_flush(self, p: subprocess.Popen):
        """flush the standard stream"""
        if p is None or not isinstance(p, subprocess.Popen):
            raise Exception(
                "subprocess.Popen object is None while dealing the stdout stream"
            )
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
                # print(f"Flush standard stream error: \nex:{traceback.format_exc()}")
            finally:
                time.sleep(1)

    def _common_args(self, account) -> list:
        """get the common args for calling the telegram.
        including: -account -target -phone"""
        _account = account  # 登陆账号
        # target = tsk._fields["datadir"]  #已登陆账号文件存储目录
        # 暂时不使用传过来的账号存储路径，直接使用本地管理的账号路径
        _target = self._t_file.as_posix()
        randomsel = random.SystemRandom()
        phone = ["HUAWEIMate10", "Xiaomi6", "SamSungGALAXYNote8", "vivox20", "OPPOR11"]
        _phone = randomsel.choice(phone)  # 设备类型
        res = [
            f"-account {_account}",
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
            f"-jar {self._jar.as_posix()}",
            f"-{cmdtype}",
        ]
        argnew.extend(args)

        # execute
        p = self._run_process(
            self._java.as_posix(),
            *argnew,
            sudo=sudo,
            rootDir=rootDir,
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
        stdout=None,
        stderr=None,
    ) -> subprocess.Popen:
        """
        run process under current operation system and return the process object.
        executable: the executable binary path.
        arg: all args in a str.
        sudo: True if sudo
        rootDir: current work dir.
        目前所有的功能都只应用于linux docker虚拟容器内
        """
        p = None
        try:
            if not os.path.exists(rootDir):
                os.makedirs(rootDir)
            cmd = "sudo "
            params = " ".join(args)
            params = f"{executable} {params}"
            cmd = cmd + params
            logmsg = cmd
            self._logger.info(logmsg)
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
        except Exception as ex:
            raise ex
        return p

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

    def _select_data(self, sql: str, pars: tuple, dbfile: str):
        conn = sqlite3.connect(dbfile)
        try:
            conn.row_factory = self._dict_factory
            conn.text_factory = self._text_factory
            c = conn.cursor()
            c.execute(sql, pars)
            res = c.fetchall()
        except:
            self._logger.error(f"Select data error, err:{traceback.format_exc()}")
            res = []
            conn.rollback()
        finally:
            conn.close()
        return res

    def _delete_data_row(self, sqlpath):
        """
        因为telegram原生数据库很大，所以需要把messages和Channels_Message
        里面的二进制data删除掉
        :param sqlpath:
        :param sql:
        :param pars:
        :return:
        """
        conn = sqlite3.connect(sqlpath)
        try:
            c = conn.cursor()
            sql1 = """
            UPDATE messages SET data=Null
            """
            c.execute(sql1)
            self._logger.info(f"Delete message binary data")
            sql2 = """
            UPDATE Channels_Message SET data=Null
            """
            c.execute(sql2)
            self._logger.info(f"Delete channels message binary data")
        except:
            self._logger.error(f"Delete binary data error,err:{traceback.format_exc()}")
            conn.rollback()
        finally:
            conn.close()
        return

    def _is_login(self, phone, globalcode):
        """
        判断账号是否需要重新登陆
        :return:
        """
        is_login_status = False
        p = None
        try:
            args = ["-file {}".format(globalcode + phone)]
            args.extend(self._common_args(phone))
            p = self._run_telegram(
                *args,
                cmdtype="find_online",
                taskid=self.task.batchid,
                # stdout=fsout,
                # stderr=fserr,
            )
            # 读取error
            process_err = threading.Thread(target=self._read_err_log, args=(p,))
            process_err.start()
            # 刷新
            process_flush = threading.Thread(target=self._std_flush, args=(p,))
            process_flush.start()
            self._stopsigin = False
            while True:
                line = p.stdout.readline()
                if line is not None and line != "":
                    msg: str = line.strip().rstrip()
                    if not msg.startswith("#"):
                        self._logger.info(f"{msg}")
                        continue
                    if "#@21" in msg or "#@22" in msg or "#@23" in msg or "#@24" in msg:
                        self._logger.info(f"result code: {msg}")
                        is_login_status = True
                        break
                    else:
                        self._logger.info(f"result code: {msg}")
                        break
        except Exception:
            self._logger.error(traceback.format_exc())
            if p is not None:
                p.kill()
        finally:
            if p is not None:
                exitcode = p.wait()
                self._logger.info(f"program return code: {str(exitcode)}")
            self._stopsigin = True
        return is_login_status

    def sms_login(self, phonenum):
        """
        description:
        telegram短信登陆方法
        param {*}
        return {*}
        """
        # 默认带了+86的
        login_result = False
        args = self._common_args(phonenum)
        p = self._run_telegram(
            *args,
            cmdtype="login",
            taskid=self.task.batchid,
            # stdout=fsout,
            # stderr=fserr,
        )
        # 读取输出
        process_login = MyThread(self._login_process, args=(p,))
        process_login.start()
        process_flush = threading.Thread(target=self._std_flush, args=(p,))
        process_flush.start()
        process_err = threading.Thread(target=self._read_err_log, args=(p,))
        process_err.start()
        try:
            if self._sectimeout > 0:
                process_login.join(self._sectimeout)
                if process_login.isAlive and process_login.is_alive():
                    self._logger.error(f"timeout sec:{self._sectimeout}")
            else:
                process_login.join()
            # 登陆程序会在这里结束，然后获取到执行结果
            login_result = process_login.get_result()
        except Exception:
            self._logger.error(traceback.format_exc())
            if p is not None:
                p.kill()
        finally:
            if p is not None:
                p.poll()
                p.terminate()
            process_flush.join()
            process_err.join()
        return login_result

    def _login_process(self, p: subprocess.Popen):
        login_result = False
        if p is None or not isinstance(p, subprocess.Popen):
            raise Exception(
                "subprocess.Popen object is None while dealing the stdout stream"
            )
        self._stopsigin = False
        try:
            while True:
                line = p.stdout.readline()
                if line is not None and line != "":
                    msg: str = line.strip().rstrip()
                    if not msg.startswith("#"):
                        self._logger.info(f"{msg}")
                        continue
                    retcode = msg
                    idx = msg.find(" ")
                    if idx < 0:
                        idx = msg.find("\t")
                    if idx > 0:
                        retcode = msg[:idx].strip().rstrip()
                    if retcode == "#@31":
                        self._logger.info(f"result code: {msg}")
                        try:
                            vercode = self.get_verifi_code()
                        except:
                            # 验证码超时做的事情
                            vercode = "00000"
                        p.stdin.write(f"{vercode}\n")
                        p.stdin.flush()
                    elif retcode == "#@36":
                        self._logger.info(f"result code: {msg}")
                    elif retcode == "#@32":
                        # 登陆成功
                        self._logger.info(f"result code: {msg}")
                        login_result = True
                        break
                    else:
                        self._logger.info(f"result code: {msg}")
                        login_result = False
                        break
        except Exception:
            self._logger.error(f"Telegram登录失败\ntraceback.format_exc()")
            login_result = False
            if p is not None:
                p.kill()
        finally:
            exitcode = p.wait()
            self._logger.info(f"program return code: {str(exitcode)}")
            self._stopsigin = True
        return login_result

    def _download_sqlitdb(self, phonenum):
        """
        这个方法是去下载数据库文件，数据库下载完成后返回的是true,
        因为涉及到多个程序操作数据库，所以需要等到数据下载完成后再去读取数据库中的数据
        update bu judy
        每次落地自己账号的时候需要去下载一遍查看是否有新的信息更新
        每次舆情监控的时候需要去下载一遍查看是否有新的信息更新
        :return:
        """
        res = False
        args = self._common_args(phonenum)
        argnew = [
            f"-jar {self._jar.as_posix()}",
            f"-{'download'}",
            f"-{'download_public_channel'}",
            "-max_size 500",
            "-max_time 10",
        ]
        argnew.extend(args)
        p = self._run_process(self._java.as_posix(), *argnew)
        # 读取error
        process_err = threading.Thread(target=self._read_err_log, args=(p,))
        process_err.start()
        # 刷新
        process_flush = threading.Thread(target=self._std_flush, args=(p,))
        process_flush.start()
        self._stopsigin = False
        try:
            while True:
                line = p.stdout.readline()
                if line is not None and line != "":
                    msg: str = line.strip().rstrip()
                    if not msg.startswith("#"):
                        self._logger.info(f"{msg}")
                        # print(msg)
                        continue
                    retcode = msg
                    idx = msg.find(" ")
                    if idx < 0:
                        idx = msg.find("\t")
                    if idx > 0:
                        retcode = msg[:idx].strip().rstrip()
                    if retcode == "#@43" or retcode == "#@2000":
                        self._logger.info(f"{msg}")
                        # print(msg)
                        download_process = self._downloadprogress.findall(msg)
                        if len(download_process) != 0:
                            cmdrecmsg = (
                                f"正在下载telegram信息，当前下载进度: {int(download_process[-1])}%"
                            )
                            self._logger.info(cmdrecmsg)
                            self._outprglog(cmdrecmsg)
                    elif retcode == "#@41":
                        self._logger.info(f"{msg}")
                        # print(msg)
                        res = True
                        # 下载完成了就结束呀
                        break
                    elif retcode == "#@1000":
                        # 出现意外情况停止
                        # 这里说下为什么会停止，因为telegram那边爆出的错误是影响下载的，但是也有可能会把数据库下载下来
                        # 所以在外面判断下，如果数据库已经下载下来了，那么就可以先把下载的数据返回回去
                        # 或者不返回回去，因为很多文件如果没有下载回来的话，那么返回数据也确实会爆出很多错误
                        # 先不改，by judy 19/12/30，不想去判断日志
                        self._logger.info(f"{msg}")
                        break
                    else:
                        pass
                        # 再增加意外的情况
        except:
            res = False
            log = "telegram信息下载出现错误，未完成本次下载"
            self._outprglog(log)
            self._logger.error(
                f"There was a problem downloading telegrambase database\nerr:{traceback.format_exc()}"
            )
        finally:
            # 最后要结束不然telegram会卡在这，导致后续的任务不会进行
            if p is not None:
                p.kill()
                p.poll()
                p.terminate()
            exitcode = p.wait()
            self._logger.info(f"program return code: {str(exitcode)}")
            self._stopsigin = True

            process_flush.join()
            process_err.join()
        # 目前测试就直接返回true
        return res
