#!/bin/bash
# DO NOT RUN THIS OUTSIDE THE CONTAINER.
# This script builds a zip file for use in AWS Lambda.
set -xe

# Clean out our drop directory
rm -rf /opt/*


apt-get update && apt-get install -y curl zip

# First, we add the SDK version that's installed in the container image
# to the requirements.txt file.
export HALO_SDK_VERSION=`pip list | grep cloudpassage | awk '{print $2}' | sed -E 's/(\(|\))//g'`
echo "cloudpassage==${HALO_SDK_VERSION}" >> /src/jira_halo_issues_sync/requirements.txt

# Fix pip
echo "Fixing pip"
apt-get remove -y python-pip
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
rm get-pip.py

# Install requirements
echo "Installing SAM"
pip3 install aws-sam-cli


# Bundle it up!
mv /src/jira_halo_issues_sync/template.yml /src/
cd /src/
sam build -b /opt/ --debug --region=us-west-2


# Bundle up the zip file
cd /opt/JiraHaloIssuesSyncFunction/
zip -r /src/JiraHaloIssuesSyncFunction.zip ./*
rm -rf /opt/*
mv /src/JiraHaloIssuesSyncFunction.zip /var/delivery/
echo "/var/delivery/ contents:"
ls /var/delivery
echo "/src/ contents:"
ls /src

# tree /src
