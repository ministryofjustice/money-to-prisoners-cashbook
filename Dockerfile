FROM ubuntu:trusty

RUN locale-gen "en_US.UTF-8"
ENV LC_CTYPE=en_US.UTF-8

RUN apt-get update && \
    apt-get install -y \
      curl software-properties-common python-software-properties

RUN curl -sL https://deb.nodesource.com/setup_4.x | bash -

RUN apt-get update && \
    apt-get install -y \
        build-essential git python3-all python3-all-dev python3-setuptools \
        libpq-dev ntp ruby ruby-dev nodejs python3-pip python-pip

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 10

WORKDIR /app

RUN npm install npm -g
RUN npm config set python python2.7
ENV NODE_PATH /usr/lib/node_modules/money-to-prisoners-cashbook/node_modules
ENV NODE_PATH $NODE_PATH:/usr/lib/node_modules
RUN npm install -g bower gulp

ADD ./conf/uwsgi /etc/uwsgi

ADD ./requirements/ /app/requirements/
RUN pip3 install -r requirements/prod.txt

ADD .bowerrc bower.json package.json README.md /app/
RUN npm install --production --unsafe-perm --global

ADD . /app
RUN gulp --production
RUN ./manage.py collectstatic --noinput

EXPOSE 8080
CMD ["/usr/local/bin/uwsgi", "--ini", "/etc/uwsgi/magiclantern.ini"]
