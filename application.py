#!/usr/bin/python2
import jlib
import sys


def main():
    logger = jlib.Logger()
    # Get config
    config = jlib.ConfigHelper()
    if not config.required_vars_are_set():
        sys.exit(1)

    # Create objects we'll interact with later
    halo = jlib.Halo(config.halo_api_key, config.halo_api_secret_key,
                     config.halo_api_hostname)
    jira = jlib.JiraLocal(config.jira_api_url, config.jira_api_user,
                          config.jira_api_token,
                          config.jira_issue_id_field,
                          config.jira_project_key,
                          config.jira_issue_type)
    determinator = jlib.Determinator(config.issue_status_closed,
                                     config.issue_close_transition,
                                     config.issue_status_hard_closed,
                                     config.issue_reopen_transition)
    formatter = jlib.Formatter()
    reconciler = jlib.Reconciler(halo, jira, config.jira_field_mapping,
                                 config.jira_field_static)

    # Get issues created, changed, deleted since starting timestamp
    msg = "Getting all Halo issues from the last {} minutes".format(config.time_range)  # NOQA
    logger.info(msg)
    halo_issues = halo.describe_all_issues(config.tstamp, config.critical_only)

    # Compare Halo issue IDs against existing Jira issues, to determine
    # what should be created, updated, closed, or reopened.
    msg = "Getting Jira issues which correspond to Halo issues."
    logger.info(msg)
    marching_orders = {}
    for x in halo_issues:
        issue_id = x["id"]
        jira_related = jira.get_jira_issues_for_halo_issue(x["id"])
        marching_orders[issue_id] = {"halo": x, "jira": jira_related}
    for x in marching_orders.keys():
        marching_orders[x]["disposition"] = determinator.get_disposition(marching_orders[x]["halo"], marching_orders[x]["jira"])

    # Reconcile.
    for issue_id, other in marching_orders.items():
        action = other["disposition"][0]
        if action == "create":
            msg = "Creating Jira issue for Halo issue ID {}".format(issue_id)
        elif action == "create_closed":
            msg = "Creating and closing Jira issue for Halo issue ID {}".format(issue_id)
        elif action == "comment":
            msg = "Commenting Jira issue for Halo issue ID {}".format(issue_id)
        elif action == "change_status":
            msg = "Transitioning Jira issue for Halo issue ID {}".format(issue_id)
        elif action == "nothing":
            logger.info("Nothing to do for Halo issue ID {}".format(issue_id))
            continue
        logger.info(msg)
        reconciler.reconcile(other["disposition"], other["halo"])
    logger.info("Done!")



if __name__ == "__main__":
    main()
