FROM buildpack-deps:latest
MAINTAINER Michael Halstead <mhalstead@linuxfoundation.org>

ENV PYTHONUNBUFFERED 1
ENV LANG en_US.UTF-8
ENV LC_ALL $LANG

## Uncomment to set proxy ENVVARS within container
#ENV http_proxy http://your.proxy.server:port
#ENV https_proxy https://your.proxy.server:port

RUN apt-get update
RUN apt-get install -y --no-install-recommends \
        apt-utils \
        locales \
	python-dev \
        python3-dev \
	python-imaging \
	netcat-openbsd \
	vim \
	&& rm -rf /var/lib/apt/lists/*
RUN echo $LANG UTF-8 > /etc/locale.gen \
    && locale-gen && update-locale LANG=$LANG
RUN curl -O https://bootstrap.pypa.io/get-pip.py \
    && python3 get-pip.py && python2 get-pip.py && rm get-pip.py
RUN pip3 install gunicorn
RUN git clone --single-branch --branch paule/otherdistro https://git.yoctoproject.org/git/layerindex-web /opt/layerindex
RUN pip3 install -r /opt/layerindex/requirements.txt
RUN pip install -r /opt/layerindex/requirements.txt
ADD docker/refreshlayers.sh /opt/refreshlayers.sh
ADD docker/updatelayers.sh /opt/updatelayers.sh
ADD docker/migrate.sh /opt/migrate.sh
ADD docker/settings.py /opt/layerindex/settings.py

## Uncomment to add a .gitconfig file within container
#ADD docker/.gitconfig /root/.gitconfig
## Uncomment to add a proxy script within container, if you choose to
## do so, you will also have to edit .gitconfig appropriately
#ADD docker/git-proxy /opt/bin/git-proxy

RUN mkdir /opt/workdir
RUN adduser --system --uid=500 layers
RUN chown -R layers /opt
USER layers

# Start Gunicorn
CMD ["/usr/local/bin/gunicorn", "wsgi:application", "--workers=4", "--bind=:5000", "--log-level=debug", "--chdir=/opt/layerindex"]
