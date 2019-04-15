Changelog
=========


v1.0
----

New
~~~
- Add NO_SVA config option to suppress SVA issues. [Ash Wilson]

  Closes #58
- Added ability to suppress comments on existing issues. [Ash Wilson]

  Closes #55
- Manage state in SSM between invocations. [Ash Wilson]

  Optionally use SSM to manage a placeholder timestamp
  between invocations.

  Closes #33
- Parameterize concurrency settings for Halo.describe_all_issues() [Ash
  Wilson]

  Closes #29
- Introduce adjustable parallelization settings. [Ash Wilson]

Changes
~~~~~~~
- Corrected tests to use state 'deactivated' [Ash Wilson]

  Closes #65
- Adding CHANGELOG.rst. [Ash Wilson]

  Closes #62
- Documenting Jira permissions validation process. [Ash Wilson]

  Closes #39
- Logging and issue retrieval improvements. [Ash Wilson]
- Performance improvements in reconciler. [Ash Wilson]
- Performance improvements in correlating Halo issues to Jira issues.
  [Ash Wilson]

  Closes #14
- Improve JQL construction for Halo issue ID field names with spaces.
  [Ash Wilson]

  Improved error logging for issue transitions- if the desired
  transition does not exist and operation fails, error logs will
  contain transitions available for issue.

  Closes #10
- Include builder for AWS Lambda. [Ash Wilson]
- Initial working commit. [Ash Wilson]

Fix
~~~
- Accept IDs or names for mapped fields. [Ash Wilson]

  Closes #48
- Improvements in filtering for initial issue ingest. [Ash Wilson]

  Improvements in logging

  Improve accuracy by using two distinct API interactions for getting
  initial list of issues.

  Closes #23

Other
~~~~~
- Initial commit. [Ash Wilson]


