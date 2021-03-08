"""
网盘文件
create by judy 2018/10/18
"""
import io
import os

from datacontract.idowndataset import Task
from .feedbackbase import DriveTreeData, EStandardDataType, FeedDataBase


class INETDISKFILE(FeedDataBase, DriveTreeData):
    """表示一个网盘文件\n
    treedataid:当前网盘文件在网站的的唯一标识，没有就自行计算md5等\n
    downloadurl:当前网盘文件的下载链接\n
    stream:当前网盘数据流，从网上下载到的\n
    filename:当前网盘文件的文件名\n
    filesize:当前网盘文件的大小，单位byte\n
    extension:当前网盘文件的后缀，没有就不填"""

    def _is_dir(self) -> bool:
        return False

    def __init__(self,
                 clientid: str,
                 tsk: Task,
                 apptype: int,
                 treedataid: str,
                 path: str,
                 downloadurl: str,
                 stream: io.IOBase,
                 filename: str = None,
                 filesize: float = 0,
                 extention: str = None):
        FeedDataBase.__init__(self, '.inetdisk_file',
                              EStandardDataType.NetDiskList, tsk, apptype,
                              clientid, False)
        if not isinstance(path, str) or path == "":
            raise Exception("Invalid param 'path' for INETDISKFILE")
        DriveTreeData.__init__(self, treedataid, path)

        if not isinstance(downloadurl, str) or downloadurl == "":
            raise Exception("Invalid param 'downloadurl' for INETDISKFILE")
        if not isinstance(stream, io.IOBase):
            raise Exception("Invalid param 'stream' for INETDISKFIEL")

        # 下载链接
        self._downloadurl: str = downloadurl  # 下载链接
        self.io_stream = stream
        self.filename: str = filename  # 文件名
        self.filesize: float = filesize  # 大小byte
        self.extension: str = extention  # 后缀
        if self.extension is None and not self.filename is None:
            self.extension = os.path.splitext(self.filename)
