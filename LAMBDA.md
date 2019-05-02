# Running in AWS Lambda

## Building the zip archive for AWS Lambda

Build the container image and run the lambda packaging script:

```
docker build -t jira_halo_issues_sync . && \
docker run \
    -v /tmp/JiraHaloIssuesSync/:/var/delivery/ \
    --entrypoint=/bin/sh  \
    jira_halo_issues_sync \
    /src/jira_halo_issues_sync/generate_lambda.sh
```

This will create the Lambda zip archive at
`/tmp/JiraHaloIssuesSync/JiraHaloIssuesSyncFunction.zip`

## Lambda configuration

* Runtime: Python2.7
* Handler: application.lambda_handler
* Memory: 256MB

### Environment variables


| Variable name            | Purpose                                                                                                           |
|--------------------------|-------------------------------------------------------------------------------------------------------------------|
| AWS_SSM_TIMESTAMP_PARAM  | SSM param for storing timestamp between invocations. Optional, defaults to `/CloudPassage-Jira/issues/timestamp`  |
| ISSUE_SYNC_MAX           | Limit the number of issues synchronized this invocation.                                                          |
| HALO_API_KEY             | API key ID with auditor permissions.                                                                              |
| HALO_API_SECRET_KEY      | API secret corresponding with HALO_API_KEY.                                                                       |
| HALO_API_HOSTNAME        | Hostname for CloudPassage Halo API.                                                                               |
| JIRA_API_USER            | Username corresponding to JIRA_API_TOKEN.                                                                         |
| JIRA_API_TOKEN           | API token with access as described in __Jira permissions__, above.                                                |
| JIRA_API_URL             | API URL for Jira instance. (https://my.jira.com)                                                                  |
| TIME_RANGE               | Number of minutes since last run of tool. Optional, defaults to 15.                                               |
| JIRA_ISSUE_ID_FIELD      | Name of field in Jira issue for Halo issue ID. Used to prevent duplicate issues in Jira.                          |
| JIRA_FIELD_MAPPING       | (Optional) See __Jira field mapping__, above.                                                                     |
| JIRA_FIELD_STATIC        | (Optional) Set static values for fields in Jira issues                                                            |
| JIRA_PROJECT_KEY         | Project key for project where all new issues will be created.                                                     |
| ISSUE_REOPEN_TRANSITION  | Use this transition name for reopening Jira issues.                                                               |
| ISSUE_CLOSE_TRANSITION   | Use this transition name for closing Jira issues.                                                                 |
| ISSUE_STATUS_CLOSED      | This state is considered closed, but re-openable.                                                                 |
| STATUS_HARD_CLOSED       | Optional, comma-separated. If issue status matches, do not reopen, create a new issue.                            |
| JIRA_ISSUE_TYPE          | Type of issue to create (bug, story, etc...).                                                                     |
| CRITICAL_ONLY            | Do not manage Jira issues for non-critical issues.                                                                |
| NO_COMMENT               | (Optional) Do not add comments to existing Jira issues.                                                           |
| NO_SVA                   | (Optional) Do not synchronize SVA issues.                                                                         |
| EXCLUDE_SERVER_SECURE    | Do not manage issues for issues associated with Server Secure. (unsupported in v1)                                |
| EXCLUDE_CONTAINER_SECURE | Do not manage issues for issues associated with Container Secure. (unsupported in v1)                             |
| EXCLUDE_CLOUD_SECURE     | Do not manage issues for issues associated with Cloud Secure. (unsupported in v1)                                 |

### Encryption

Retrieval of KMS-encrypted environment variables (encryption in transit) is
supported for `HALO_API_KEY`, `HALO_API_SECRET_KEY`, `JIRA_API_USER`, and
`JIRA_API_TOKEN`. This tool expects encrypted environment variables for the
four aforementioned variables. However, if decryption fails, the actual values
of these fields will be used.

### Use of AWS SSM for managing timestamp between invocations

If AWS authentication information is present in environment variables
(`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) and the `AWS REGION` environment
variable is set, this tool will attempt to take a starting timestamp from SSM,
and will ignore the TIME_RANGE setting.
