FROM ubuntu:20.04

MAINTAINER MuSiShui <zhangjieepic@gmail.com>

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update
RUN apt-get install -y nginx supervisor

# Setup flask application
RUN mkdir -p /deploy/app
COPY app /deploy/app
RUN pip3 install -r /deploy/app/requirements.txt

# Setup nginx
# RUN rm /etc/nginx/sites-enabled/default
# COPY flask.conf /etc/nginx/sites-available/
# RUN ln -s /etc/nginx/sites-available/flask.conf /etc/nginx/sites-enabled/flask.conf
# RUN echo "daemon off;" >> /etc/nginx/nginx.conf

# Setup supervisord
RUN mkdir -p /var/log/supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY gunicorn.conf /etc/supervisor/conf.d/gunicorn.conf

# Start processes
CMD ["/usr/bin/supervisord"]
