FROM docker.io/halotools/python-sdk:ubuntu-16.04_sdk-1.2.3_py-2.7
MAINTAINER toolbox@cloudpassage.com

ENV HALO_API_HOSTNAME=api.cloudpassage.com

RUN mkdir -p /src/jira_halo_issues_sync/

COPY ./ /src/jira_halo_issues_sync/

WORKDIR /src/jira_halo_issues_sync/

RUN pip install -r requirements.txt

CMD /usr/bin/python /src/jira_halo_issues_sync/application.py
