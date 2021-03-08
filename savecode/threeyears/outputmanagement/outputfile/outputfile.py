"""output file"""

# -*- coding:utf-8 -*-

import io
import os
import shutil
import threading
import traceback

from commonbaby.helpers import helper_file
from commonbaby.mslog import MsLogger, MsLogManager

from datacontract.datamatcher import DataMatcher
from datacontract.outputdata import OutputData
from ..outputerbase import OutputerBase
from ..outputstandardconfig import OutputDataConfig


class Outputfile(OutputerBase):
    """输出文件数据\n
    description:当前输出器描述，必填，且每个输出器唯一\n
    platform: 当前输出器所属平台\n
    targetdir: 目标目录"""

    _logger: MsLogger = MsLogManager.get_logger("Outputerfile")
    _tmpdir: str = "./_servertmp"

    tmpdir_locker = threading.RLock()
    outdir_locker = threading.RLock()

    def __init__(
            self,
            description: str,
            platform: str,
            datamatcher: DataMatcher = None,
            maxsegcount: int = 1000,
            enc: str = "utf-8",
            outputdir: str = "./_returndata",
            tmpdir: str = "./_servertmp",
    ):
        OutputerBase.__init__(
            self,
            description=description,
            platform=platform,
            datamatcher=datamatcher,
            maxsegcount=maxsegcount,
            enc=enc,
        )

        if not isinstance(outputdir, str) or outputdir == "":
            raise Exception("Invalid param 'outputdir'")
        if not isinstance(tmpdir, str) or tmpdir == "":
            raise Exception("Invalid param 'tmpdir'")

        if not os.path.isdir(outputdir):
            os.makedirs(outputdir)
        self._outputdir: str = outputdir
        self._outputdir_locker = threading.RLock()

        self._tmpdir: str = tmpdir
        Outputfile._tmpdir = tmpdir
        if not os.path.isdir(tmpdir):
            os.makedirs(tmpdir)

    def _output_sub(self,
                    data: OutputData,
                    bs: bytes,
                    datastd: OutputDataConfig,
                    stm: io.RawIOBase = None) -> bool:
        """输出到文件"""
        with self._outputdir_locker:
            return Outputfile._output_to_file(data, bs, datastd,
                                              self._outputdir, stm)

    @classmethod
    def output_to_file(cls, data: OutputData, datastd: OutputDataConfig,
                       targetdir: str) -> bool:
        """输出数据到指定目录"""
        res: bool = False
        try:
            if not isinstance(data, OutputData):
                cls._logger.error("Invalid OutputData object: {}".format(data))
                return res

            if not isinstance(datastd, OutputDataConfig):
                cls._logger.error(
                    "Invalid OutputDataStandard: {}".format(datastd))
                return res

            stm = data.get_stream()

            if not isinstance(stm, io.IOBase) or not stm.readable():
                succ: bool = True
                for b in cls._get_mutiple_bs(data, datastd):
                    if not cls._output_to_file(data, b, datastd, targetdir):
                        succ = False
                        break
                res = succ
            else:
                b: bytes = cls._get_single_bs(data, datastd, stm)
                return cls._output_to_file(data, b, datastd, targetdir, stm)

        except Exception:
            cls._logger.error("Output data error: {} {}\n{}".format(
                data._platform, datastd._uniquename, traceback.format_exc()))
        return res

    @classmethod
    def _output_to_file(
            cls,
            data: OutputData,
            bs: bytes,
            datastd: OutputDataConfig,
            targetdir: str,
            stm: io.RawIOBase = None,
    ) -> bool:
        """输出到指定目录\n
        bs:要输出的数据\n
        datastd:数据对应的数据标准，用于构建文件名等\n
        targetdir:目标目录\n
        stm: 附带的数据流"""
        res: bool = False
        tmppath: str = None
        outfi: str = None
        try:
            with cls.tmpdir_locker:
                # 临时路径
                tmppath: str = cls._get_datapath(cls._tmpdir, datastd)
                if not isinstance(tmppath, str) or tmppath == "":
                    return res

                with open(tmppath, mode="wb") as fs:
                    fs.write(bs)
                    if not stm is None and stm.readable():
                        # stm.readinto(fs)
                        readlen = 1024 * 1024 * 1024
                        while True:
                            buf = stm.read(readlen)
                            if buf is None:
                                break
                            readcount = len(buf)
                            fs.write(buf)
                            if readcount < readlen:
                                break

            # 加了一个验证步骤..
            # 后面如果要搞扩展输出方式，
            # 应吧输出到临时，和输出到目标分成两个函数，
            # 在两个函数调用的中间加一个验证步骤，各自实现

            if not data.validate_file(tmppath):
                # 不打日志了，错误数据直接不输出
                cls._logger.debug("Corrupted data: {}".format(tmppath))
                if os.path.isfile(tmppath):
                    os.remove(tmppath)
                return res

            with cls.outdir_locker:
                outfi: str = cls._get_datapath(targetdir, datastd)
                shutil.move(tmppath, outfi)
            res = True
        except Exception:
            if not tmppath is None and tmppath != "" and os.path.isfile(
                    tmppath):
                os.remove(tmppath)
            if not outfi is None and outfi != "" and os.path.isfile(outfi):
                os.remove(outfi)

            cls._logger.error("Output data segments sub error: {}".format(
                traceback.format_exc()))
        return res

    @classmethod
    def _get_datapath(cls, di: str, datastd: OutputDataConfig) -> str:
        """构建数据完整路径\n
        di: 父目录路径\n
        datastd: 数据标准配置\n"""
        res: str = None

        # if not isinstance(lk, threading.RLock):
        #     raise Exception("Invalid filename creation locker")

        if not os.path.exists(di):
            os.makedirs(di)
        dataname = cls._get_dataname(datastd)
        if not isinstance(dataname, str) or dataname == "":
            cls._logger.error("Construct dataname error: {}".format(dataname))
            return res
        datapath = os.path.join(di, dataname)
        while os.path.exists(datapath):
            dataname = cls._get_dataname(datastd)
            if not isinstance(dataname, str) or dataname == "":
                cls._logger.error(
                    "Construct dataname error: {}".format(dataname))
                return res
            datapath = os.path.join(di, dataname)
        datapath = os.path.abspath(datapath)

        return datapath

    def output_move_file(self, platform: str, srcfi: str) -> bool:
        """根据platform，把指定srcfi源文件移动到对应平台的回传目录中，
        返回是否移动成功True/False。\n
        若未找到指定平台的回传目录，则返回False。"""
        res: bool = False
        tarfi: str = None
        try:
            if not os.path.exists(srcfi):
                self._logger.error(
                    "Source file not exists for output move file: {}".format(
                        srcfi))
                return res

            di, fi = os.path.split(srcfi)

            tarfi = os.path.abspath(os.path.join(self._outputdir, fi))
            while os.path.exists(tarfi):
                tarfi = helper_file.rename_file_by_number_tail(tarfi)

            with self._outputdir_locker:
                shutil.move(srcfi, tarfi)

            res = True
        except Exception:
            self._logger.error(
                "Output move file error:\nplatform:{}\nsrcfi:{}\ntarfi:{}\nerror:{}"
                    .format(self._platform, srcfi, tarfi, traceback.format_exc()))
        return res
