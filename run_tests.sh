#!/bin/bash

apt-get update && apt-get install -y git curl

/usr/bin/python -mpip install -r /src/jira_halo_issues_sync/requirements-testing.txt

echo "Testing requires the following environment variables to be set:"
echo "HALO_API_KEY"
echo "HALO_API_SECRET_KEY"
echo "JIRA_API_URL"
echo "JIRA_API_USER"
echo "JIRA_API_TOKEN"
echo "JIRA_ISSUE_ID_FIELD"
echo "JIRA_PROJECT_KEY"
echo "ISSUE_CLOSE_TRANSITION"
echo "ISSUE_REOPEN_TRANSITION"
echo "JIRA_ISSUE_TYPE"

if [ -z "${CC_TEST_REPORTER_ID}" ]; then
  /usr/bin/python -m py.test --cov=jlib --cov-report=term-missing --profile test/
  export TEST_STATUS=$?
else
  apt-get update && apt-get install -y git
  curl -L https://codeclimate.com/downloads/test-reporter/test-reporter-latest-linux-amd64 > ./cc-test-reporter
  chmod +x ./cc-test-reporter
  ./cc-test-reporter before-build
  /usr/bin/python -m py.test --cov-report=xml --cov-report=term-missing --cov=jlib --profile test/
  export TEST_STATUS=$?
  ./cc-test-reporter after-build --exit-code ${TEST_STATUS}
fi
exit ${TEST_STATUS}
