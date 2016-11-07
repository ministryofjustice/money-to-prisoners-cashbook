FROM ubuntu:trusty

RUN echo "Europe/London" | cat > /etc/timezone && dpkg-reconfigure --frontend noninteractive tzdata
RUN locale-gen "en_GB.UTF-8"
ENV LC_CTYPE=en_GB.UTF-8

RUN apt-get update && \
    apt-get install -y software-properties-common python-software-properties

RUN add-apt-repository -y ppa:chris-lea/node.js

RUN apt-get update && \
    apt-get install -y \
        build-essential git python3-all python3-all-dev python3-setuptools \
        curl libpq-dev ntp gettext libpcre3-dev nodejs python3-pip python-pip libfontconfig \
        libfreetype6

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 10

WORKDIR /app
RUN mkdir -p /app/mtp_cashbook/assets
RUN mkdir -p /app/static

RUN npm install npm -g
RUN npm config set python python2.7

# cache node modules, unless requirements change
ADD ./package.json /app/package.json
RUN npm set progress=false

RUN pip3 install -U setuptools pip wheel virtualenv
RUN virtualenv -p python3.4 venv

# cache python packages, unless requirements change
ADD ./requirements /app/requirements
RUN venv/bin/pip install -r requirements/docker.txt

ADD . /app
RUN make build python_requirements=requirements/docker.txt

EXPOSE 8080
CMD make uwsgi python_requirements=requirements/docker.txt
