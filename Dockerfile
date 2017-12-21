FROM buildpack-deps:latest
MAINTAINER Michael Halstead <mhalstead@linuxfoundation.org>

EXPOSE 80
ENV PYTHONUNBUFFERED 1
## Uncomment to set proxy ENVVARS within container
#ENV http_proxy http://your.proxy.server:port
#ENV https_proxy https://your.proxy.server:port

RUN apt-get update
RUN apt-get install -y --no-install-recommends \
	python-pip \
	python-mysqldb \
	python-dev \
	python-imaging \
	python3-pip \
	python3-mysqldb \
	python3-dev \
	python3-pil \
	rabbitmq-server \
	locales \
	netcat-openbsd \
	vim \
	&& rm -rf /var/lib/apt/lists/*
RUN sed -i 's/^# *\(en_US.UTF-8\)/\1/' /etc/locale.gen && locale-gen
ENV LANG en_US.UTF-8
RUN pip install --upgrade pip
RUN pip install gunicorn
RUN pip install setuptools
RUN pip3 install setuptools
RUN mkdir /opt/workdir
COPY . /opt/layerindex
RUN pip install -r /opt/layerindex/requirements.txt
RUN pip3 install -r /opt/layerindex/requirements.txt
COPY settings.py /opt/layerindex/settings.py
COPY docker/updatelayers.sh /opt/updatelayers.sh
COPY docker/migrate.sh /opt/migrate.sh
COPY docker/start.sh /opt/start.sh

## Uncomment to add a .gitconfig file within container
#ADD docker/.gitconfig /root/.gitconfig
## Uncomment to add a proxy script within container, if you choose to
## do so, you will also have to edit .gitconfig appropriately
#ADD docker/git-proxy /opt/bin/git-proxy

# Run start script

CMD ["/opt/start.sh"]

