"""
autotask dbip mmdb下载，由server控制
"""
# from ..autopluginbase import AutoPluginBase
#
#
# class Dbip(AutoPluginBase):
#
#     def __init__(self):
#         AutoPluginBase.__init__(self)
#
#     def start(self):
#         pass

import gzip
import shutil
from pathlib import Path

import requests
from commonbaby.mslog import MsLogger, MsLogManager

_logger: MsLogger = MsLogManager.get_logger("DBIP")

filename = Path('./dbip.mmdb.gz')
url = 'https://download.db-ip.com/free/dbip-city-lite-2019-08.mmdb.gz'
count = 0
with requests.get(url, stream=True) as r:
    r.raise_for_status()
    with filename.open('wb') as f:
        for chunk in r.iter_content(chunk_size=1024 * 1024):
            count += 1
            _logger.info(f'{count} times Downloaded 1Mb, and waiting...')
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)

with gzip.open('./dbip.mmdb.gz', 'rb') as f_in:
    with open('dbip.mmdb', 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
