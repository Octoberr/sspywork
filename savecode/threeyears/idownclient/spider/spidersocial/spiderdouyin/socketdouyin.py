"""douyin socket"""

# -*- coding:utf-8 -*-

import socket
import threading
import time
import traceback

from commonbaby.helpers import helper_str
from commonbaby.mslog import MsLogger, MsLogLevel, MsLogLevels

from datacontract.idowndataset import Task


class SocketDouyin:
    """为抖音插件提供命令通信服务。\n
    dip: 目标服务ip，直接写字符串'x.x.x.x'\n
    dport: 目标服务端口，int类型，0~65535\n
    timeoutsec: 数据读取超时时间，float，单位毫秒。传None表示不超时或超时时间未定义（走系统超时时间），传0表示完全不阻塞（要烂）\n
    logger: 可以把外部的MsLogger对象传进来打印日志，也可以不传，反正会把服务端返回的消息msg返回"""

    def __init__(self,
                 dip: str,
                 dport: int,
                 timeoutsec: float = 5,
                 logger: MsLogger = None):
        if not isinstance(dip, str) or dip == "":
            raise ValueError("dip is invalid for SocketDouyin.")
        if not isinstance(dport, int) or dport < 0 or dport > 65535:
            raise ValueError("dport is invalid for SocketDouyin.")

        self._dip: str = dip
        self._dport: int = dport
        self._timeoutsec = timeoutsec
        self._logger: MsLogger = logger

        # 用于通讯的sock对象，外面可以拿去用
        # 但是要注意业务流程，不要弄烂了。
        self._socket = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=0,
            fileno=None)
        self._socket.settimeout(self._timeoutsec)
        # 简单状态值，避免重复发送
        self._stack_locker = threading.Lock()
        self._stack: dict = {
            self.connect: False,
            self.send_phonenum: False,
            self.send_verify_code: False,
            self.send_download: False,
            self.send_exit: False
        }

        self.__connected: bool = False
        self.__connected_locker = threading.Lock()
        # 记录当前正在执行的task，必须一个账号一个账号地发命令。
        self._tasks: list = []
        self.__curr_task: Task = None
        self.__task_locker = threading.Lock()

    def connect(self) -> (bool, str):
        """尝试链接指定服务端dip:dport，并返回是否连接成功bool。
        只需要连接一次，永远不断开"""
        succ: bool = False
        msg = "failed"
        try:
            if self.__connected:
                succ = True
                msg = 'OK'
                return (succ, msg)

            with self.__connected_locker:
                if self.__connected:
                    succ = True
                    msg = 'OK'
                    return (succ, msg)

                address = (self._dip, self._dport)
                self._socket.connect(address)
                msg = "OK"
                succ = True
                self.__connected = True

        except Exception:
            succ = False
            msg = "Connect douyin server({}:{}) error: {}".format(
                self._dip, self._dport, traceback.format_exc())
            self.__log(msg)
        return (succ, msg)

    def send_phonenum(self, phone, task: Task) -> (bool, str):
        """向抖音服务传入电话号码，并返回元组(是否传入成功,服务返回的结果字符串)(bool,str)"""
        succ: bool = False
        msg: str = "failed"
        try:
            self.__check_task(task)
            if not self.__check_status(self.send_phonenum):
                return (succ, msg)

            if not isinstance(phone, str) or phone == "":
                msg = "Phone number is None or empty"
                return (succ, msg)
            self._curr_phone = phone

            # send
            sendmsg: str = "hello\nphone_number\n{}\n".format(self._curr_phone)
            self._socket.sendall(sendmsg.encode('utf-8'))

            # recv
            ret_should_be: str = 'phone_number_ok\n'
            succ, msg = self.__read_msg(ret_should_be)
            if msg.lower() == ret_should_be:
                succ = True

        except Exception:
            msg = "Send phone number to douyin server error: {} {}".format(
                phone, traceback.format_exc())
            self.__log(msg)

        return (succ, msg)

    def send_verify_code(self, code: str, task: Task) -> (bool, str):
        """向抖音服务传入验证码，并返回元组(是否传入成功,服务返回的结果字符串)(bool,str)"""
        succ: bool = False
        msg: str = "failed"
        try:
            self.__check_task(task)
            if not self.__check_status(self.send_verify_code):
                return succ

            if not isinstance(code, str) or code == "":
                msg = "Sms verify code is None or empty"
                return (succ, msg)

            # send
            sendmsg: str = "hello\nphone_code\n{}\n".format(code)
            self._socket.sendall(sendmsg.encode('utf-8'))

            # recv
            ret_should_be: str = 'phone_code_ok\n'
            succ, msg = self.__read_msg(ret_should_be)
            if msg.lower() == ret_should_be:
                succ = True

        except Exception:
            msg = "Send VERIFY_CODE to douyin server error: {} {} {}".format(
                self._curr_phone, code, traceback.format_exc())
            self.__log(msg)
        return (succ, msg)

    def send_download(self, task: Task,
                      buffsize: int = 1024 * 1024) -> (bool, bytes):
        """向抖音服务传入下载命令，并返回元组（是否传入成功，文件流）。外部
        拿到文件流后写到本地文件中，就是一个sqlite，然后从里面读数据出来。
        返回(bool,bytes)"""
        succ: bool = False
        data: bytes = None
        msg: str = "failed"
        try:
            self.__check_task(task)
            if not self.__check_status(self.send_download):
                return succ

            # send
            sendmsg: str = "hello\nchat_info\nchat_info\n"
            self._socket.sendall(sendmsg.encode('utf-8'))


            # recv
            print("sleep 2 seconds .........")
            time.sleep(2)
            succ, data = self.__read_data()
            if not succ:
                return (succ, msg)

            # recv msg
            ret_should_be = 'chat_info_ok\n'
            succ, msg = self.__read_msg(ret_should_be)
            print("sleep 5 seconds ...........")
            time.sleep(5)
            if msg.lower() == ret_should_be:
                succ = True

        except Exception:
            msg = "Send DOWNLOAD to douyin server error: {} {}".format(
                self._curr_phone, traceback.format_exc())
            self.__log(msg)
        return (succ, data)

    def send_exit(self, task: Task) -> (bool, str):
        """向抖音服务传入验证码，并返回元组(是否传入成功,服务返回的结果字符串)(bool,str)"""
        succ: bool = False
        msg: str = "failed"
        try:
            self.__check_task(task)
            if not self.__check_status(self.send_exit):
                return succ

            # send
            sendmsg: str = "hello\nlogout\nlogout\n"
            self._socket.sendall(sendmsg.encode('utf-8'))

            # recv
            ret_should_be: str = 'logout_ok\n'
            succ, msg = self.__read_msg(ret_should_be)
            if msg.lower() == ret_should_be:
                succ = True

        except Exception:
            msg = "Send exit to douyin server error: {} {}".format(
                self._curr_phone, traceback.format_exc())
            self.__log(msg)
        finally:
            # 只要调这个，就把currenttask移除
            with self.__task_locker:
                if self.__curr_task in self._tasks:
                    self._tasks.remove(self.__curr_task)
                self.__curr_task = None
            # 清除上一个任务的调用情况
            with self._stack_locker:
                self._stack.clear()
                self._stack: dict = {
                    self.connect: False,
                    self.send_phonenum: False,
                    self.send_verify_code: False,
                    self.send_download: False,
                    self.send_exit: False
                }

        return (succ, msg)

    def __read_msg(self, retmsg: str) -> (bool, str):
        """读取指定文本内容，返回是否成功读取到,以及读取到的内容（bool,str）"""
        succ: bool = False
        readmsg: str = None
        try:
            if helper_str.is_none_or_empty(retmsg):
                self.__log("Read msg param 'retmsg' is empty")
                return (succ, readmsg)

            retmsglen = len(retmsg)

            retdata: bytes = self.__read_bytes(retmsglen)
            if retdata is None or len(retdata) != retmsglen:
                return (succ, 'read bytes from server failed')

            if not retdata is None:
                readmsg = retdata.decode('utf-8')

            if readmsg.lower() == retmsg:
                succ = True

        except Exception:
            succ = False
            readmsg = 'Read msg from server error: {} {}'.format(
                self._curr_phone, traceback.format_exc())
            self.__log(readmsg)

        return (succ, readmsg)

    def __read_data(self) -> (bool, bytes):
        """从服务端读取数据，返回（是否读取成功，数据bytes）"""
        succ: bool = False
        data: bytes = None
        try:

            # 拿数据长度
            bslen: bytes = self.__read_bytes(4)
            if bslen is None or len(bslen) != 4:
                return (succ, data)
            filen = int.from_bytes(bslen, byteorder='big')
            print("data length: {}".format(filen))
            # 拿数据
            data: bytes = self.__read_bytes(filen)
            if data is None or len(data) != filen:
                return (succ, None)

            succ = True

        except Exception:
            self.__log("Read data from server failed: {}:{}".format(
                self._dip, self._dport))
        return (succ, data)

    def __read_bytes(self, retmsglen: int) -> bytes:
        """从服务端读取指定长度字节数，返回bytes"""
        retdata: bytes = bytes()
        readlen = 0
        while True:
            try:
                to_read_len = retmsglen - readlen
                if to_read_len < 1:
                    break

                retdata += self._socket.recv(to_read_len)
                readlen += len(retdata)

            except socket.timeout:
                self.__log("Read timeout")
                break

        return retdata

    def __check_task(self, task: Task, timeoutsec: float = -1):
        """检查是否为当前正在执行的账号，如果不是就等待，如果超时就报错。"""
        if not isinstance(task, Task):
            raise Exception("Task is invalid")
        sleptsec: int = 0
        while True:
            with self.__task_locker:
                if self.__curr_task is None:
                    self.__curr_task = task
                    self._tasks.append(self.__curr_task)
                    break
                elif self.__curr_task == task:
                    break
                else:
                    time.sleep(1)
                    sleptsec += 1
            if timeoutsec > 0 and sleptsec >= timeoutsec:
                raise Exception(
                    "Wait for previous task timeout: {} seconds".format(
                        timeoutsec))

    def __check_status(self, key) -> bool:
        """检查调用顺序，调一次就会将指定key的调用标记设为True。
        返回是否检查通过：True通过/False不通过"""
        res: bool = False
        if not self._stack.__contains__(key):
            self.__log("Key not found in stack dict: {}".format(key))
            return res

        with self._stack_locker:
            if not self._stack[key]:
                self._stack[key] = True
                res = True
            else:
                self.__log("Method '{}' already called".format(key))

        return res

    def __log(self, msg: str, lvl: MsLogLevel = MsLogLevels.INFO):
        """"""
        if helper_str.is_none_or_empty(msg):
            return
        if isinstance(self._logger, MsLogger):
            self._logger.log(msg, lvl)
