# This dockerfile uses the alpine:latest image

# Author: Nekomi-CN

FROM ubuntu:20.04

ADD app/ /

RUN apt-get update; \
    apt-get install -y python3-pip; \
    pip install -r requirements.txt

CMD [ "python", "steam-auto-change-country.py" ]
