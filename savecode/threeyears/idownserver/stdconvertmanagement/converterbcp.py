"""bcp standard converter"""

# -*- coding:utf-8 -*-

import os
import traceback
import zipfile

from commonbaby.helpers import helper_dir, helper_file

from datacontract.inputdata import InputData
from datacontract.idowndataset.task import Task
from dataparser import DataParser

from .converterbase import ConverterBase, DataSeg


class ConverterBcp(ConverterBase):
    """转换Bcp格式4gcookie到标准Task"""

    def __init__(self,
                 uniquename,
                 fields: dict,
                 extendfields: dict,
                 extensions: list,
                 enc: str = 'utf-8',
                 tmpdir: list = r'./_servertmp'):

        ConverterBase.__init__(self, uniquename, fields, extendfields)

        if not isinstance(extensions, list) or len(extensions) < 1:
            raise Exception("Specified ConverterBcp extension is invalid")
        self._extensions: list = [e.strip(".") for e in extensions]

        self._enc: str = 'utf-8'
        if isinstance(enc, str) and not enc == '':
            self._enc = enc

        self._tmpdir = os.path.abspath(
            os.path.join('./_servertmp',
                         "convert_{}".format(self._uniquename)))
        if isinstance(tmpdir, str) and not tmpdir == "":
            self._tmpdir = os.path.abspath(
                os.path.join(tmpdir, "convert_{}".format(self._uniquename)))
        self._check_exists_tmp_folder()
        if not os.path.exists(self._tmpdir) or not os.path.isdir(self._tmpdir):
            os.makedirs(self._tmpdir)

    def match_data(self, data: InputData) -> bool:
        """匹配数据"""
        res: bool = False
        try:
            if data is None:
                raise Exception("Data is None.")

            if isinstance(
                    data.extension,
                    str) and data.extension.strip('.') in self._extensions:
                res = True

        except Exception:
            self._logger.error(
                "Match data error:\ndata:%s\nex:%s" % data._source,
                traceback.format_exc())
        return res

    def _check_exists_tmp_folder(self):
        """检查临时文件夹，如果有已存在的东西，需要处理掉"""
        # 先暂定为删除
        helper_dir.remove_dirs(self._tmpdir)

    def _convert(self, data: InputData) -> iter:
        """将中心下发的任务转换为自有的通用任务结构Task体枚举（一个文件可能有多个任务段）"""
        try:
            if data.stream is None or not data.stream.readable():
                self._logger.error(
                    "Data stream is None when trying to convert to standard Task: %s"
                    % data._source)
                return

            todir = os.path.join(self._tmpdir,
                                 data.name.strip(data.extension).strip('.'))
            while os.path.exists(todir):
                todir = helper_file.rename_file_by_number_tail(todir)

            with data._load_stream(mode='rb', enc=None) as fs:
                # 解压
                with zipfile.ZipFile(fs, 'r') as f:
                    for zfile in f.namelist():
                        f.extract(zfile, todir)

                # 处理task
                for pp in os.listdir(todir):
                    bfname, bfext = os.path.splitext(pp)
                    bfpath = os.path.join(todir, pp)
                    # 不是bcp的删掉
                    if not bfext.endswith("bcp"):
                        os.remove(bfpath)
                        continue
                    bffi = os.path.join(todir, pp)
                    # 一个bcp里有多行，每行都是一个task
                    for task in self._bcp_deal(bffi, data):
                        if task is None:
                            continue
                        yield task

            # 删除临时文件
            helper_dir.remove_dirs(todir)
            #

        except Exception:
            self._logger.error("Convert data to Task error:\ndata:%s\nex:%s" %
                               (data._source, traceback.format_exc()))
            if not data is None:
                data.on_complete(False)

    def _bcp_deal(self, bcpfi: str, data: InputData) -> iter:
        """读取bcp文件行，构建task任务"""
        try:
            segindex = 0
            segline = 0
            succ = True
            with open(bcpfi, 'r', encoding=self._enc) as fs:
                for seg in DataParser.parse_bcp_data(fs):
                    try:
                        seg: DataSeg = seg
                        # 必要字段
                        self._add_required_fields(seg, data)

                        # 根据host拿apptype
                        if not seg.contains_key("apptype"):
                            apptype = self._get_apptype(seg._fields, data)
                            if not apptype is None:
                                seg.append_to_fields('apptype', apptype)

                        # 验证字段有效性
                        if not self._validation_fields(seg, data):
                            succ = False
                            continue

                        task: Task = Task(seg._fields)
                        task.segindex = segindex
                        task.segline = segline
                        segline += 1
                        segindex += 1
                        yield task
                    except Exception as ex:
                        succ = False
                        self._logger.error(
                            "Parse one line in bcp file error:\ndata:%s\nerror:%s"
                            % (bcpfi, ex))

        except Exception:
            succ = False
            self._logger.error("Deal bcp file error:\nfile:%s\nerror:%s" %
                               (bcpfi, traceback.format_exc()))
        finally:
            if not succ:
                data.on_complete(False)

        return
