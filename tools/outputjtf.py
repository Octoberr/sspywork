"""
输出json数据到文件
可能会用到多个地方所以多以静态方法为主
create by judy 2019/06/26
"""
import shutil
from pathlib import Path
import uuid
import json
import threading


class Outputjtf(object):
    outdir_locker = threading.RLock()

    @staticmethod
    def output_json_to_file(data, tmppath: Path, outpath: Path, suffix: str, ensure_ascii=False):
        """
        先把数据输出到缓存文件夹，然后再移动到输出文件夹
        :param ensure_ascii:
        :param data:
        :param tmppath:
        :param outpath:
        :param suffix:
        :return:
        """
        # if not isinstance(data, dict):
        #     raise Exception("Output data is not dict, can not convert to json.")
        if not isinstance(tmppath, Path):
            raise Exception("Tmpdir path should be Path object")
        if not isinstance(outpath, Path):
            raise Exception("Outdir should be Path object")
        # 获取需要写入的json数据
        json_data = data
        if isinstance(data, dict):
            json_data = json.dumps(data, ensure_ascii=ensure_ascii)
        with Outputjtf.outdir_locker:
            # 这个tmpname为None主要是为了，当写入文件出错的时候，删除创建的0KB的文件
            tmpname = None
            try:
                # --------------------------------------------tmppath
                tmpname = tmppath / f'{uuid.uuid1()}.{suffix}'
                while tmpname.exists():
                    tmpname = tmppath / f'{uuid.uuid1()}.{suffix}'
                # 这里的文件体大了后会出现无法写完的bug，不过应该不是这里的bug
                tmpname.write_text(json_data, encoding='utf-8')

                # ------------------------------------------outputpath
                outname = outpath / f'{uuid.uuid1()}.{suffix}'
                while outname.exists():
                    outname = outpath / f'{uuid.uuid1()}.{suffix}'
                # 将tmppath 移动到outputpath
                #tmpname.replace(outname)
                shutil.move(tmpname.as_posix(), outname.as_posix())
                tmpname = None
                return outname.name
            except Exception as error:
                print(data)
                raise Exception(error)

            finally:
                if tmpname is not None:
                    tmpname.unlink()
