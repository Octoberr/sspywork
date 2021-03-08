Readme file

# build 命令

python setup.py bdist_wheel

# 2020.07.30 - 2.2.0

- 新增`helper_process.py`，包括对进程的帮助函数；
- 新增其他很多帮助函数；
- 添加 crypto 依赖等；
- 包括之前的所有更新；

# 2019.10.19 - 1.0.0

- 新增 `responseIO.__len__` 函数，当 HTTP 响应中包含`content-length`字段时可获取 http 流长度，否则报错。
