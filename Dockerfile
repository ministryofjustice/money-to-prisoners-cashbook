FROM ubuntu:trusty

RUN echo "Europe/London" > /etc/timezone  &&  dpkg-reconfigure -f noninteractive tzdata

RUN apt-get update && \
    apt-get install -y software-properties-common python-software-properties

RUN add-apt-repository -y ppa:chris-lea/node.js

RUN apt-get update && \
    apt-get install -y \
        build-essential git python3-all python3-all-dev python3-setuptools \
        curl libpq-dev ntp ruby ruby-dev nodejs python3-pip python-pip

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 10

WORKDIR /app

RUN gem install sass --no-rdoc --no-ri
RUN npm install -g bower gulp

ADD ./conf/uwsgi /etc/uwsgi

ADD ./requirements/ /app/requirements/
RUN pip3 install -r requirements/prod.txt

ADD . /app

RUN npm install --unsafe-perm
RUN gulp
RUN ./manage.py collectstatic --noinput

EXPOSE 8080
CMD ["/usr/local/bin/uwsgi", "--ini", "/etc/uwsgi/magiclantern.ini"]
