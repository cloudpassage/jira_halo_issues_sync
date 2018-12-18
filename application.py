#!/usr/bin/python2
import boto3
import jlib
import json
import os
import sys
from base64 import b64decode
from multiprocessing.dummy import Pool as ThreadPool


def main():
    logger = jlib.Logger()
    # Get config
    config = jlib.ConfigHelper()
    if not config.required_vars_are_set():
        sys.exit(1)

    # Create objects we'll interact with later
    halo = jlib.Halo(config.halo_api_key, config.halo_api_secret_key,
                     config.halo_api_hostname)

    # Get issues created, changed, deleted since starting timestamp
    msg = "Getting all Halo issues from the last {} minutes".format(config.time_range)  # NOQA
    logger.info(msg)
    halo_issues = halo.describe_all_issues(config.tstamp, config.critical_only)

    # Compare Halo issue IDs against existing Jira issues, to determine
    # what should be created, updated, closed, or reopened.
    msg = "Getting Jira issues which correspond to Halo issues."
    logger.info(msg)
    marching_orders = get_marching_orders(config, halo_issues)

    # Reconcile.
    reconcile_marching_orders(config, marching_orders)

    # for issue_id, other in marching_orders.items():

    logger.info("Done!")
    return {"result": json.dumps(
                {"message": "Halo/Jira issue sync complete",
                 "total_issues": len(marching_orders.items())})}


def reconcile_marching_orders(config, marching_orders):
    packed_list = [(config, x) for x in marching_orders.items()]
    reconciler_helper = reconcile_issue
    pool = ThreadPool(7)
    pool.map(reconciler_helper, packed_list)
    pool.close()
    pool.join()
    return


def reconcile_issue(reconcile_bundle):
    config, item = reconcile_bundle
    issue_id, other = item
    logger = jlib.Logger()
    halo = jlib.Halo(config.halo_api_key, config.halo_api_secret_key,
                     config.halo_api_hostname)
    jira = jlib.JiraLocal(config.jira_api_url, config.jira_api_user,
                          config.jira_api_token,
                          config.jira_issue_id_field,
                          config.jira_project_key,
                          config.jira_issue_type)
    reconciler = jlib.Reconciler(halo, jira, config.jira_field_mapping,
                                 config.jira_field_static)
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
    logger.info(msg)
    reconciler.reconcile(other["disposition"], other["halo"])


def get_marching_orders(config, issue_list):
        """Map Halo issue IDs to thread pool for checking Jira issues."""
        determinator = jlib.Determinator(config.issue_status_closed,
                                         config.issue_close_transition,
                                         config.issue_status_hard_closed,
                                         config.issue_reopen_transition)
        packed_list = [(config, x) for x in issue_list]
        issue_correlator_helper = jira_issue_correlator
        pool = ThreadPool(5)
        correlated_issues = pool.map(issue_correlator_helper, packed_list)
        pool.close()
        pool.join()
        marching_orders = {x["halo"]["id"]: {"disposition": determinator.get_disposition(x["halo"], x["jira"]),  # NOQA
                                             "halo": x["halo"],
                                             "jira": x["jira"]}
                           for x in correlated_issues}
        return marching_orders


def jira_issue_correlator(get_tup):
    """Gets Jira issues related to a Halo issue ID.
    Args:
        get_tup(tuple): First item in tuple is the config object.  The second
            is the Halo issue object of interest.
    Returns:
        dict: Halo issue information
    """
    config, halo_issue = get_tup
    jira = jlib.JiraLocal(config.jira_api_url, config.jira_api_user,
                          config.jira_api_token,
                          config.jira_issue_id_field,
                          config.jira_project_key,
                          config.jira_issue_type)
    jira_related = jira.get_jira_issues_for_halo_issue(halo_issue["id"])
    return {"halo": halo_issue, "jira": jira_related}


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
