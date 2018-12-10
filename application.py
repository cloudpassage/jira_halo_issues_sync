#!/usr/bin/python2
import boto3
import jlib
import json
import os
import sys
from base64 import b64decode


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
        marching_orders[x]["disposition"] = determinator.get_disposition(marching_orders[x]["halo"], marching_orders[x]["jira"])  # NOQA

    # Reconcile.
    for issue_id, other in marching_orders.items():
        action = other["disposition"][0]
        if action == "create":
            msg = "Creating Jira issue for Halo issue ID {}".format(issue_id)
        elif action == "create_closed":
            msg = "Creating and closing Jira issue for Halo issue ID {}".format(issue_id)  # NOQA
        elif action == "comment":
            msg = "Commenting Jira issue for Halo issue ID {}".format(issue_id)
        elif action == "change_status":
            msg = "Transitioning Jira issue for Halo issue ID {}".format(issue_id)  # NOQA
        elif action == "nothing":
            logger.info("Nothing to do for Halo issue ID {}".format(issue_id))
            continue
        logger.info(msg)
        reconciler.reconcile(other["disposition"], other["halo"])
    logger.info("Done!")
    return {"result": json.dumps(
                {"message": "Halo/Jira issue sync complete",
                 "total_issues": len(marching_orders.items())})}


def lambda_handler(event, context):
    """We expect credentials to be encrypted if we're running in Lambda."""
    logger = jlib.Logger()
    kms = boto3.client('kms')
    encrypted_vars = ["HALO_API_KEY", "HALO_API_SECRET_KEY",
                      "JIRA_API_USER", "JIRA_API_TOKEN"]
    for encrypted_var in encrypted_vars:
        try:
            encrypted_value = os.getenv(encrypted_var)
            decrypted_value = kms.decrypt(CiphertextBlob=b64decode(encrypted_value))['Plaintext']  # NOQA
            os.environ[encrypted_var] = decrypted_value
            msg = "Set var {} to decrypted value with length {}".format(encrypted_var, len(decrypted_value))  # NOQA
            logger.warn(msg)
        except (kms.exceptions.InvalidCiphertextException, TypeError) as e:
            msg = "Error decrypting {} with KMS, will try plaintext: {}".format(encrypted_var, e)  # NOQA
            logger.error(msg)
    return main()


if __name__ == "__main__":
    main()
