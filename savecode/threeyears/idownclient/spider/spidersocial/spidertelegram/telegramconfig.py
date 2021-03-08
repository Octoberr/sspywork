""""
telegram的配置，仅作用于当前的telegram插件
create by judy 2018/10/29
"""
from pathlib import Path


class TelegramConfig(object):
    def __init__(
            self,
            accountsdata: str = None,
            javapath: str = None,
            telegram: str = None,
            timesex: float = None,
    ):
        # 存放telegram资源的文件夹
        telegramfiles: Path = Path('./resource/telegramsource')
        telegramfiles.mkdir(exist_ok=True, parents=True)
        # 存储下载的账号数据
        self.accountsdata = telegramfiles
        if accountsdata is not None and accountsdata != '':
            self.accountsdata = Path(accountsdata)
        self.accountsdata.mkdir(exist_ok=True, parents=True)  # 自定义的文件夹不应该没有创建

        # 存储java环境
        self.javapathdir = telegramfiles / 'jdk1.8.0_181'
        self.javapath = self.javapathdir / 'bin/java'
        if javapath is not None and javapath != '':
            self.javapath = Path(javapath)

        # 存储telegram.jar
        self.telegram = telegramfiles / 'telegram.jar'
        if telegram is not None and telegram != '':
            self.telegram = Path(telegram)

        self.timesec = 24 * 60 * 60
        if timesex is not None:
            self.timesec = timesex
