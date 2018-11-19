FROM docker.io/halotools/python-sdk:ubuntu-16.04_sdk-1.2.1_py-2.7
MAINTAINER toolbox@cloudpassage.com

ENV HALO_API_HOSTNAME=api.cloudpassage.com

RUN mkdir /src

COPY ./ /src

WORKDIR /src

RUN pip install -r requirements.txt

CMD /usr/bin/python /src/application.py
