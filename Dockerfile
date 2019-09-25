FROM docker.io/halotools/python-sdk:ubuntu-18.04_sdk-latest_py-3.6
MAINTAINER toolbox@cloudpassage.com

ENV HALO_API_HOSTNAME=api.cloudpassage.com

RUN mkdir -p /src/jira_halo_issues_sync/

COPY ./ /src/jira_halo_issues_sync/

WORKDIR /src/jira_halo_issues_sync/

RUN pip3 install -r requirements.txt

CMD /usr/bin/python3 /src/jira_halo_issues_sync/application.py
