# syntax=docker/dockerfile:1
FROM jlesage/baseimage-gui:ubuntu-22.04-v4.5.2 as builder

ENV APT_SOURCE_HOST "mirrors.ustc.edu.cn"

RUN <<EOT
sed -i "s/archive.ubuntu.com/${APT_SOURCE_HOST}/g" /etc/apt/sources.list
apt-get update -y
apt-get install -y software-properties-common locales
add-apt-repository universe
locale-gen zh_CN.UTF-8
apt-get update -y
apt-get install -y libcairo2-dev build-essential fonts-noto-color-emoji libgl1 fonts-wqy-zenhei python3-pip python-is-python3 python3-pyqt5
apt autoremove -y
rm -rf /var/lib/apt/lists/*
python -V
pip -V 
EOT

FROM builder as app
ARG TARGETPLATFORM
# Set environment variables.
ENV APP_NAME="MDCX" \
    USER_ID=0 \
    GROUP_ID=0 \
    LANG=zh_CN.UTF-8 \
    TZ=Asia/Shanghai
ARG VERSION=next

ADD . /app
COPY ./scripts/11-app-init.sh /etc/cont-init.d/

WORKDIR /app
EXPOSE 5800 5900

RUN <<EOT
python3 -m pip install --upgrade pip
python3 -m pip install --no-cache-dir -r requirements.txt -i https://pypi.douban.com/simple
set-cont-env APP_VERSION ${VERSION}
set-cont-env DOCKER_IMAGE_VERSION 1.0.${VERSION}
EOT

COPY ./scripts/startapp.sh /startapp.sh
