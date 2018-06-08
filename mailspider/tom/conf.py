"""
tom爬虫的配置文件
create by swm
2018/06/06
"""
from pathlib import Path
# 当前文件夹
file = Path(__file__).parent

config = {}
config['bshead'] = '=?UTF-8?b?'
config['emlfloder'] = file/Path('../mailfloder')
config['contactsfloder'] = file/Path('../contacts')
