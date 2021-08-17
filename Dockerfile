FROM ubuntu
# includes Python 3.8.5

# Linux Updates
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get upgrade -y

# Sysytem Depencencies
ENV PYTHONUNBUFFERED=1
RUN apt-get -yqq install python3-pip python3-dev
RUN python3 -m pip install --upgrade pip

RUN python3 -m pip install setuptools wheel Cython
RUN python3 -m pip install Fortuna --no-cache-dir

# App Dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app app
COPY .env .env

# Network Settings
EXPOSE 8000
CMD gunicorn app.main:APP --bind 0.0.0.0:8000
