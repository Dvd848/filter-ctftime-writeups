# syntax=docker/dockerfile:1

FROM python:3.8.10-slim-buster

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

RUN apt-get update && apt-get install -y \
    net-tools \
    wget \
    firefox-esr \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir /geckodriver

RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.29.1/geckodriver-v0.29.1-linux64.tar.gz -O /geckodriver/geckodriver.tar.gz

RUN tar -xvf /geckodriver/geckodriver.tar.gz --directory=/geckodriver

RUN echo "export PATH=/geckodriver:$PATH" >> ~/.bashrc

# docker build --tag filter-ctftime-writeups:latest .
# docker run -it -p 5000:5000 -v ${PWD}:/app --name filterctftimewriteups --rm --env-file credentials.env filter-ctftime-writeups:latest /bin/bash