FROM ubuntu:20.04

MAINTAINER MuSiShui <zhangjieepic@gmail.com>

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update
RUN apt-get install -y python3 python3-pip supervisor gunicorn

# Setup flask application
RUN mkdir -p /deploy/app
COPY app /deploy/app
RUN pip3 install -r /deploy/app/requirements.txt

# Start processes
CMD ["python3", "/deploy/app/SteamFreeGame.py"]
