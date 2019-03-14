# jira_halo_issues_sync

Synchronize Halo issues with Jira

[![Build Status](https://travis-ci.com/cloudpassage/jira_halo_issues_sync.svg?branch=master)](https://travis-ci.com/cloudpassage/jira_halo_issues_sync)

[![Maintainability](https://api.codeclimate.com/v1/badges/96396b330e4b5b954563/maintainability)](https://codeclimate.com/github/cloudpassage/jira_halo_issues_sync/maintainability)

[![Test Coverage](https://api.codeclimate.com/v1/badges/96396b330e4b5b954563/test_coverage)](https://codeclimate.com/github/cloudpassage/jira_halo_issues_sync/test_coverage)

## What it does:

This tool synchronizes
[CloudPassage Halo issues](https://blog.cloudpassage.com/2017/05/30/issues-and-policies-with-halo/)
with Jira issues.

New issues discovered in Halo cause new issues to be created in Jira.

Updated issues in Halo will cause comments to be created in the corresponding
Jira issue, containing information from the updated issue.

Closed issues in Halo will cause the corresponding Jira issue to be closed.

Issues which have been prematurely closed will be re-opened if the Halo issue
still exists, and issues which are re-opened will cause the corresponding Jira
issue to re-open.

Version 1 of this integration will only support issues associated with the
CloudPassage Halo ServerSecure module (FIM, CSM, SVM, LIDS). Future versions
may support ContainerSecure- and CloudSecure-related issues.

## How it works

This integration is delivered as Python tool, enclosed in a Docker container
image. Sure, you can run the enclosed tool by itself... but running it outside
the container image or Lambda (see LAMBDA.md) is not supported.

The container is run periodically, and retrieves the status of all issues which
have been opened, closed, or updated since the last time the tool was run. The
tool then synchronizes Halo issue status with the status of the corresponding
Jira issues.

### Issue created

When an issue is created, the integration will search for an existing issue in
Jira by Halo issue ID. If a issue already exists with the issue ID, the
operation will be treated as an `Issue updated` action. If no issue exists with
the Halo issue ID, the integration will create the issue in Jira according to
the field mappings defined in the runtime configuration, and having the status
defined by ${NEW_ISSUE_STATUS} (see below).

### Issue updated

When a Halo issue is updated, the integration will search for the original
issue in Jira. If no issue can be found in Jira for the associated Halo issue
ID, this will be treated as an `Issue created` action. If a Jira issue is found
for the updated issue, the integration will add a comment to the Jira issue
containing the latest findings. These updates may happen as frequently as your
configured scan interval.

### Issue resolved

When a Halo issue is resolved, the integration searches Jira for the
corresponding issue, adds a comment to the issue with resolution information,
and triggers the ${ISSUE_CLOSE_TRANSITION} in Jira (see below). If no Jira
issue can be found with a corresponding Halo issue ID, this will be treated as
an `Issue created`, then an `Issue resolved` event. This will effectively create
and close a issue for tracking purposes in Jira.

### Issue reopened

When a Halo issue is re-opened, the integration searches for the closed Jira
issue with the corresponding Halo issue ID. If none can be found, this is
treated as an `Issue created` event. If the original issue can be located, an
${ISSUE_REOPEN_TRANSITION} (see below) is triggered and a comment is added
to the Jira issue containing information about why the issue was re-opened.
If the issue has a status which matches one in ${HARD_CLOSED_STATUS}, a new
issue will be opened.



## Requirements

* CloudPassage Halo API key (with auditor permissions)
* Jira Cloud API token (see __Jira permissions__, below)
* Scheduling system
  * Recommended: [CloudPassage Cortex](https://github.com/cloudpassage/cortex)
  * If you're not using Cortex, you need a task scheduler and a Docker engine
  to run the container.
* Optional: Run in AWS Lambda!  See [LAMBDA.md](LAMBDA.md)

## Running (stand-alone)

1. Obtain Jira and CloudPassage Halo API credentials
1. Set environment variables (see __Environment variables__, below.)
1. Run the container:
```
docker run \
    -it \
    --rm \
    --read-only \
    -e ENV_VAR:${ENV_VAR} \ # one of these for every environment variable
    docker.io/halotools/jira_halo_issues_sync:latest
```

## Notes

### Workflow considerations

In order to route Jira issues to the appropriate people, we expect that a
Jira workflow will perform the routing based on the Jira issue's contents, upon
the creation of the issue in Jira.

This integration will create all Jira issues in the same Jira project, and the
implementer will use Jira workflows together with issue attributes (like
`asset_group_path`, detailed below) to route issues to other projects or
to assign issues to specific Jira users.

The process whereby this integration updates or closes Jira issues does not
search for issues within a specific project. It expects a searchable field to
exist which contains the Halo issue ID, and as long as the issue exists
somewhere in Jira (in any project), the integration will attempt to update the
Jira issue. This is also the process by which the integration prevents the
creation of duplicate issues for the same issue.

In large environments with many Halo issues, this integration can produce a
great number of issues in Jira. Consider creating workflows in Jira to group
issues into epics, or create relevant dashboards which group issues based on
group paths, issue type, or some other commonality relevant for the person
tasked with resolving vulnerabilities.

### Jira permissions

This tool creates, updates, and performs workflow transitions on issues in Jira.
The issue type and status transitions applied to issues created by this tool
are completely configurable, as are field mappings from Halo to Jira. As such,
it is not possible for us to create specific policy guidance which will allow
you to maintain the principle of least privilege when configuring this
synchronization tool.

Every mature Jira implementation is different, and complexity can grow
over time. Once you have a user account configured with the permissions you
believe to be appropriate to create, update, and transition issues according
to your workflow's requirements (and this tool's configuration), it makes sense
to log in as that user and step through all the transitions you want the tool
to perform manually. This will allow you to catch edge cases before deployment,
and will make it easier to maintain the principle of least privilege. A
preliminary validation process might look like this:

* Log in as the user account which the integration will be using
* Create a test issue of type `JIRA_ISSUE_TYPE`, with a unique string in the
field named by `JIRA_ISSUE_ID_FIELD`.
* Perform a search for the unique string you used in `JIRA_ISSUE_ID_FIELD`,
and confirm that exactly one issue is found in Jira.
* Add a comment to the test issue.
* Transition the issue using the transition named in `ISSUE_CLOSE_TRANSITION`.
* Transition the issue using the transition named in `ISSUE_REOPEN_TRANSITION`.
* If your workflow automation migrates Jira issues between projects, you should
confirm that the integration account can perform the transitions mentioned above
in each of the projects where a Halo issue may be migrated.


### Jira field mapping

Mapping Halo issues to Jira fields can be accomplished by setting and passing
the ${JIRA_FIELD_MAPPING} into the container. This field should be formatted
like this: `halo_field_1:jira_field_1;halo_field_2:jira_field_2`. Similarly,
the ${JIRA_FIELD_STATIC} mapping separates keys from values with a colon (:)
and separates key/value pairs with a semicolon (;).

Available Halo fields are:

| Halo field             | Purpose                                                                                                   |
|------------------------|-----------------------------------------------------------------------------------------------------------|
| asset_group_name       | Name of Halo group containing the asset.                                                                  |
| asset_group_path       | Halo group path for asset associated with this issue.                                                     |
| asset_type             | Server, Container, CSP Asset. Currently, only Server is supported.                                        |
| issue_critical         | `True` or `False`.                                                                                        |
| issue_created_at       | ISO8601 timestamp for when issue was first created.                                                       |
| issue_rule_key         | issue_type::rule_number::rule_name. See {here](https://api-doc.cloudpassage.com/help#issues) for details. |
| issue_type             | lids, csm, fim, sva, sam, fw, or agent.                                                                   |
| issue_id               | Unique ID of this issue                                                                                   |
| issue_policy_name      | Name of Halo policy associated with this issue.                                                           |
| server_csp_provider    | Name of CSP provider, as detected by Halo agent                                                           |
| server_csp_account_id  | CSP Account ID, as detected by Halo agent                                                                 |
| server_csp_instance_id | CSP instance ID, as detected by Halo agent                                                                |
| server_id              | Halo Server ID                                                                                            |
| server_hostname        | Hostname for server, as detected by Halo agent.                                                           |
| server_state           | State of host, as reported by Halo agent.                                                                 |

### Environment variables

| Variable name            | Purpose                                                                                           |
|--------------------------|---------------------------------------------------------------------------------------------------|
| CRITICAL_ONLY            | Do not manage Jira issues for non-critical issues. (Default: False)                               |
| NO_COMMENT               | Do not add comments to already-existing Jira issues.                                              |
| DESCRIBE_ISSUES_THREADS  | Number of Halo issues to enrich from Halo API concurrently. Optional, default 10                  |
| DETERMINATOR_THREADS     | Number of Halo issues to compare against Jira simultaneously. Optional, default 5                 |
| RECONCILER_THREADS       | Number of Halo issues to reconcile to Jira simultaneously. Optional, default 7.                   |
| HALO_API_KEY             | API key ID with auditor permissions.                                                              |
| HALO_API_SECRET_KEY      | API secret corresponding with HALO_API_KEY.                                                       |
| HALO_API_HOSTNAME        | Hostname for CloudPassage Halo API. Defaults to api.cloudpassage.com.                             |
| JIRA_API_USER            | Username corresponding to JIRA_API_TOKEN.                                                         |
| JIRA_API_TOKEN           | API token with access as described in __Jira permissions__, above.                                |
| JIRA_API_URL             | API URL for Jira instance. (https://my.jira.com)                                                  |
| TIME_RANGE               | Number of minutes since last run of tool. Optional, defaults to 15.                               |
| JIRA_ISSUE_ID_FIELD      | Name of field in Jira issue for Halo issue ID. Used to prevent duplicate issues in Jira.          |
| JIRA_FIELD_MAPPING       | (Optional) See __Jira field mapping__, above. \*                                                  |
| JIRA_FIELD_STATIC        | (Optional) Set static values for fields in Jira issues                                            |
| JIRA_PROJECT_KEY         | Project key for project where all new issues will be created.                                     |
| ISSUE_REOPEN_TRANSITION  | Use this transition name for reopening Jira issues.                                               |
| ISSUE_CLOSE_TRANSITION   | Use this transition name for closing Jira issues.                                                 |
| ISSUE_STATUS_CLOSED      | This state is considered closed, but re-openable.                                                 |
| STATUS_HARD_CLOSED       | Optional, comma-separated. If issue status matches, do not reopen, create a new issue.            |
| JIRA_ISSUE_TYPE          | Type of issue to create (bug, story, etc...).                                                     |
| EXCLUDE_SERVER_SECURE    | Do not manage issues for issues associated with Server Secure. (unsupported in v1)                |
| EXCLUDE_CONTAINER_SECURE | Do not manage issues for issues associated with Container Secure. (unsupported in v1)             |
| EXCLUDE_CLOUD_SECURE     | Do not manage issues for issues associated with Cloud Secure. (unsupported in v1)                 |
