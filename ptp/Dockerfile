FROM ubuntu:24.04

ENV TZ="Asia/Yekaterinburg"
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN mkdir /ptp

RUN apt update && apt -y upgrade && apt -yq install nginx git supervisor make build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev\
    libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python3-openssl \
    net-tools vim uwsgi uwsgi-plugin-python3 nodejs npm
RUN git clone 'https://github.com/pyenv/pyenv.git' /ptp/.pyenv
RUN git clone 'https://github.com/pyenv/pyenv-virtualenv.git' /ptp/.pyenv/plugins/pyenv-virtualenv

ENV PYENV_ROOT="/ptp/.pyenv"
ENV PATH="$PYENV_ROOT/bin:$PATH"

RUN /ptp/.pyenv/bin/pyenv install 3.14.0
RUN /ptp/.pyenv/bin/pyenv virtualenv 3.14.0 ptp

ENV LC_ALL="en-US.UTF-8"
ENV LANG="en-US.UTF-8"
ENV LANGUAGE="en-US.UTF-8"

# Copy backend
COPY ptp /ptp

# Copy frontend
COPY front /ptp/front

WORKDIR /ptp

RUN chmod 755 /ptp/init.sh

RUN /ptp/.pyenv/versions/3.14.0/envs/ptp/bin/python -m pip install --upgrade pip

RUN /ptp/.pyenv/versions/ptp/bin/pip3 install -r requirements.txt

RUN /ptp/.pyenv/versions/ptp/bin/python3 manage.py collectstatic --noinput

# Build Vue frontend
WORKDIR /ptp/front
RUN npm install && npm run build

WORKDIR /ptp

RUN ln -s /ptp/ptp.conf /etc/nginx/conf.d/ptp.conf
