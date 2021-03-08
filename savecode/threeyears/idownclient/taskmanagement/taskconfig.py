"""
有关task的配置文件
create by judy 2018/10/09
"""
from pathlib import Path


class Taskconfig(object):

    @property
    def inputpath_str(self):
        """
        返回输入文件位置的字符串
        :return:
        """
        return self.inputpath.as_posix()

    @property
    def successpath_str(self):
        """
        返回任务处理成功的字符串
        :return:
        """
        return self.successpath.as_posix()

    @property
    def errorpath_str(self):
        """
        返回任务处理失败的字符串
        :return:
        """
        return self.errorpath.as_posix()

    @property
    def tmppath_str(self):
        """
        返回任务处理暂存目录的字符串
        :return:
        """
        return self.tmppath.as_posix()

    @property
    def outputpath_str(self):
        """
        返回输出文件位置的字符串
        :return:
        """
        return self.outputpath.as_posix()

    def __init__(self,
                 sqlitpath: str = None,
                 inputpath: str = None,
                 successpath: str = None,
                 errorpath: str = None,
                 outputpath: str = None,
                 tmppath: str = None,
                 collectclienttimes: int = None,
                 buffsize: int = None,
                 rootdriver: str = None,
                 concurrent_number: int = None):

        # idown文件夹
        filepath = Path(__file__)
        rootdir = filepath.parents[2]

        # sqlit文件夹
        self.sqlitpath: Path = rootdir / '_clientdb'
        if sqlitpath is not None and sqlitpath != '':
            self.sqlitpath = Path(sqlitpath)
        # 初始化时自动创建要使用的文件
        self.sqlitpath.mkdir(exist_ok=True)

        # 输入目录
        self.inputpath: Path = rootdir / '_clientinput'
        if inputpath is not None and inputpath != '':
            self.inputpath = Path(inputpath)
        self.inputpath.mkdir(parents=True, exist_ok=True)

        # 任务处理成功目录
        self.successpath: Path = rootdir / '_clientsuccess'
        if successpath is not None and successpath != '':
            self.successpath = Path(successpath)
        self.successpath.mkdir(exist_ok=True)

        # 任务处理错误目录
        self.errorpath: Path = rootdir / '_clienterror'
        if errorpath is not None and errorpath != '':
            self.errorpath = Path(errorpath)
        self.errorpath.mkdir(exist_ok=True)

        # 输出文件夹
        self.outputpath: Path = rootdir / '_clientoutput'
        if outputpath is not None and outputpath != '':
            self.outputpath = Path(outputpath)
        self.outputpath.mkdir(exist_ok=True)

        # 状态数据输出目录
        # self.statusoutputdir: Path = rootdir / '_clientoutput'
        # if statusoutputdir is not None and statusoutputdir != '':
        #     self.statusoutputdir = Path(statusoutputdir)
        # self.statusoutputdir.mkdir(exist_ok=True)

        # 缓存文件夹
        self.tmppath: Path = rootdir / '_clienttmpdir'
        if tmppath is not None and tmppath != '':
            self.tmppath = Path(tmppath)
        self.tmppath.mkdir(exist_ok=True)

        # 获取当前代码使用的硬盘根路径
        self.driver: Path = filepath.parts[0]
        if rootdriver is not None and rootdriver != '':
            self.driver: Path = rootdriver

        # client基础信息采集时间间隔
        self.collect_client_times = 5
        if collectclienttimes is not None:
            self.collect_client_times = collectclienttimes

        self.buffsize = 1024 * 1024  # 1M
        if buffsize is not None:
            self.buffsize = buffsize

        # 同时并发处理的任务数
        self.concurrent_number = 5
        if concurrent_number is not None:
            self.concurrent_number = concurrent_number
