"""
twitter爬虫的配置文件
create by swm
2018/06/13
"""
from pathlib import Path

# 当前文件夹
file = Path(__file__).parent
logfile = file/'log'

config = {}
config['logpath'] = logfile
config['twitterpath'] = file/'twitter'