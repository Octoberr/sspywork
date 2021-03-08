FROM python:3.7.3

# If you prefer miniconda:
#FROM continuumio/miniconda3

LABEL Name=idownserver Version=0.0.1 

COPY ./resource/packages /home/idownserver/resource/packages
COPY ./resource/requirements.txt /home/idownserver/resource/
WORKDIR /home/idownserver

COPY ./apt/sources.list /etc/apt/sources.list

RUN apt update \
    && apt install -y libgl1-mesa-glx
# Using pip:
# 升级pip
RUN pip install --upgrade pip -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
# 安装本地的
RUN pip install ./resource/packages/commonbaby*.whl -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
RUN pip install -r ./resource/requirements.txt -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

CMD ["python", "server.py"]
