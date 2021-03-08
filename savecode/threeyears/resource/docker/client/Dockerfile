FROM python:3.7.9
ENV DEBIAN_FRONTEND noninteractive
ENV GO_ENV /usr/local/go/bin
ENV ZGRAB2_ENV /usr/local/go/go/src/github.com/zmap/zgrab2/
ENV NODE_ENV /usr/local/node-v12.16.1-linux-x64/bin
ENV PATH="${GO_ENV}:${ZGRAB2_ENV}:${NODE_ENV}:${PATH}"
#ENV OPENSSL_CONF /home/idownclient/openssl.config

COPY ./resource /home/idownclient/resource
WORKDIR /home/idownclient

# 以下2句在vps上不需要，目前需手动注释掉
# COPY ./apt/sources.list /etc/apt/sources.list
# RUN apt-key adv --recv-keys --keyserver keyserver.ubuntu.com 3B4FE6ACC0B21F32 \
#     && apt-key adv --recv-keys --keyserver keyserver.ubuntu.com 7EA0A9C3F273FCD8

# ！！！！！！！！提示：
# 下面的依赖安装顺序最好不要动。
# 因为Chrome是离线安装的，有些依赖可能会出问题，
# 所以把Chrome放在其他在线安装之后

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y sudo \
    # python:3.7.9 already contains the newest openssl
    # && sudo apt install build-essential checkinstall zlib1g-dev -y \
    # && apt-get install -y openssl \
    && apt install -y libgl1-mesa-glx \
    && sudo apt-get install -y curl \
    # dnsutils install
    && apt-get install -y dnsutils \
    && echo 'dnsutils ok' \
    # zmap install
    && apt-get install -y zmap \
    && zmap --version \
    && sudo apt-get install -y libgbm-dev \
    && sudo apt-get install -y ttf-wqy-microhei ttf-wqy-zenhei xfonts-wqy

# nmap install
RUN sudo dpkg -i ./resource/nmap/nmap_7.91-2_amd64.deb \
    && echo 'nmap ok'

# wappalyzer install: wappalyzer依赖于googlechrome，没有安装chrome无法获取到数据
# RUN curl -sL https://deb.nodesource.com/setup_12.x | sudo -E bash - \
#     && sudo apt-get install -y nodejs \
#     && npm i -g wappalyzer --unsafe-perm \
#     && npm i wappalyzer --save  \
#     && echo 'wappalyzer ok'

# masscan
# RUN tar -zxvf ./resource/masscan/masscan.tar.gz \
#     && apt-get -y install git gcc make libpcap-dev \
#     && cd masscan/ \
#     && make \
#     && sudo make install \
#     && echo 'masscan ok, end of building.' \
#     # 这个会把进了路径build所以需要出来
#     && cd ..

# telegram decompress scan 扫描的server不需要这个,telegram的资源都在resource下，不再需要解压到目标文件夹，by judy 2020/06/30
#RUN mkdir -p ./idownclient/spider/spidersocial/spidertelegram/telegramfiles/telegram/ \
#    && cp -u ./resource/telegramsource/telegram.jar ./idownclient/spider/spidersocial/spidertelegram/telegramfiles/telegram/telegram.jar \
#    && mkdir -p ./idownclient/spider/spidersocial/spidertelegram/telegramfiles/javapath/ \
#    && tar -zxvf ./resource/telegramsource/jdk-8u181-linux-x64.tar.gz -C ./idownclient/spider/spidersocial/spidertelegram/telegramfiles/ \
#    && mv -u ./idownclient/spider/spidersocial/spidertelegram/telegramfiles/jdk1.8.0_181/* ./idownclient/spider/spidersocial/spidertelegram/telegramfiles/javapath/ \
#    && rm -rf ./idownclient/spider/spidersocial/spidertelegram/telegramfiles/jdk1.8.0_181 \
#    && echo 'telegram ok'

# 在线安装google-chrome
RUN sudo dpkg -i ./resource/webdriver/google-chrome-stable_current_amd64.deb; exit 0
RUN sudo apt-get -y install -f \
    && chmod u+x ./resource/webdriver/chromedriver \
    && google-chrome-stable --version

# 离线安装google-chrome
# install google-chrome offline 扫描的server也不需要这个
#RUN tar -zxvf ./resource/webdriver/chrome-deps.tar.gz -C ./resource/webdriver/ \
#    && dpkg --force-all -i ./resource/webdriver/chrome-deps/* \
#    && dpkg -i ./resource/webdriver/google-chrome-stable_current_amd64.deb \
#    && chmod u+x ./resource/webdriver/chromedriver \
#    && google-chrome-stable --version


# zgrab2 install:
RUN tar -zxvf ./resource/zgrab2/go1.12.9.linux-amd64.tar.gz -C /usr/local \
    && go version \
    && tar -zxvf ./resource/zgrab2/root-go.tar.gz -C /usr/local/go/ \
    && echo 'zgrab2 ok' 


# pip update VPS上不需要用aliyun安装
# RUN pip install --upgrade pip -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com \
#     && pip install ./resource/packages/commonbaby*.whl -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com \
#     && pip install ./resource/packages/partdownload*.whl -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com \
#     && pip install ./resource/packages/geoiploc*.whl -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com \
#     && pip install ./resource/packages/pluginbase*.whl -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com \
#     && pip install ./resource/packages/wafw00f*.whl -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com \
#     && pip install -r ./resource/requirements.txt -i http://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

RUN pip install --upgrade pip \
    && pip install ./resource/packages/commonbaby*.whl \
    && pip install ./resource/packages/partdownload*.whl \
    && pip install ./resource/packages/geoiploc*.whl \
    && pip install ./resource/packages/pluginbase*.whl \
    && pip install ./resource/packages/wafw00f*.whl \
    && pip install -r ./resource/requirements.txt

# for remote debug ↓ start ####################

# # SSH
# RUN apt-get -y install openssh-server vim htop
# RUN mkdir -p /var/run/sshd

# # authorize SSH connection with root account
# RUN sed -i '/^#/!s/PermitRootLogin .*/PermitRootLogin yes/' /etc/ssh/sshd_config
# RUN sudo service ssh restart

# # change password root
# RUN echo "root:docker"|chpasswd

# # install py env
# RUN python -m pip install pylint yapf rope

# # there is a problem says zgrab2 not found
# RUN ln -s /usr/local/go/go/src/github.com/zmap/zgrab2/zgrab2 /usr/bin/zgrab2

# for remote debug ↓ end ####################

CMD ["python", "client.py"]
