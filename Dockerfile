# This dockerfile uses the alpine:latest image

# Author: Nekomi-CN

FROM ubuntu:20.04

ADD app/ /

RUN sed -i "s/http:\/\/deb.debian.org/https:\/\/mirrors.tuna.tsinghua.edu.cn/g" /etc/apt/sources.list; \
    sed -i "s/http:\/\/security.debian.org/https:\/\/mirrors.tuna.tsinghua.edu.cn/g" /etc/apt/sources.list; \
    apt-get update; \
    apt-get install -y --no-install-recommends python3-pip; \
    rm -rf /var/lib/apt/lists/*; \
    pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple some-package

CMD [ "python", "steam-auto-change-country.py" ]
