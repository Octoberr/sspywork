"""
网盘目录结构
create by judy 2018/10/18
"""

import io
import json

from datacontract.idowndataset import Task
from .feedbackbase import DriveTreeData, EStandardDataType, FeedDataBase


class INETDISKFILELIST(FeedDataBase, DriveTreeData):
    """表示一个网盘文件结构目录树\n
    此数据会在内部自行拼接json以表示目录树结构，此json
    会作为当前数据的数据体输出\n
    treedataid:当前网盘目录的唯一标识，没有就填url什么的，只要保证是唯一的即可。\n
    url:当前网盘目录的访问链接\n
    name:当前网盘目录的名称\n
    path:当前网盘目录的路径（磁盘路径格式，比如： /文件/图片/）"""

    def _is_dir(self) -> bool:
        return True

    def __init__(
            self,
            clientid: str,
            tsk: Task,
            apptype: int,
            userid: str,
            treedataid: str,
            url: str,
            name: str,
            path: str = '/',
    ):
        FeedDataBase.__init__(self, '.inetdisk_filelist',
                              EStandardDataType.NetDiskList, tsk, apptype,
                              clientid, False)
        DriveTreeData.__init__(self, treedataid, path)

        if userid is None:
            raise Exception("Userid cant be None.")
        if not isinstance(url, str) or url == "":
            raise Exception("Invalid param 'url' for INETDISKFILELIST")

        self._userid = userid
        # 当前目录的url链接
        self._url: str = url
        # 当前目录的名称
        self._name: str = name
        # 其他可选字段
        self.islocked: bool = False  #当前目录是否上锁/需要密码
        self.isprivate: bool = False  #当前目录是否是私有的

    def _get_write_lines(self) -> str:
        lines = ''
        lines += 'userid:{}\r\n'.format(self._userid)
        # 此为整个目录树所在根目录，
        # 只有在最外层根目录调用时才会执行此函数拿writelines
        # 此函数后面会弃用。。
        lines += 'path:/\r\n'
        lines += '\r\n'
        return lines

    def _get_io_stream(self) -> io.RawIOBase:
        """子类实现时，返回当前数据的文件体，二进制流"""
        tree = self._get_tree_json()
        if tree is None:
            raise Exception(
                "Parse drive tree failed: treedataid={} name={}".format(
                    self._treedataid, self._name))

        # 目前暂时没有遇到一个目录树json结构都超级大，甚至是GB级别的，
        # 后面遇到了，可能需要使用json的什么Encoder先流式写入临时文件，
        # 然后返回一个文件流作为中间数据流。。。
        jsonstr: str = json.dumps(tree).encode().decode('unicode_escape')
        stm = io.BytesIO(jsonstr.encode('utf-8'))
        return stm

    def _get_current_tree_json(self) -> dict:
        '''子类实现时，拼接一个字典，存放当前DriveTreeData的
        除了self._treedataid以外的相关信息，键和要统一！
        例如：\n
        {
            "name":"xxx",
            "url":"xxxx"
        }'''
        res: dict = {}
        res['url'] = self._url
        res['name'] = self._name
        res['isdir'] = 1 if self.is_dir else 0
        res['islocked'] = 1 if self.islocked else 0
        res['isprivate'] = 1 if self.isprivate else 0

        return res
