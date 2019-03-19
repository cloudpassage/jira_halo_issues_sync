#!/usr/bin/python2
import boto3
import datetime
import jlib
import json
import os
import sys
from base64 import b64decode


def main():
    logger = jlib.Logger()
    starting_timestamp = datetime.datetime.now().isoformat()
    # Get config
    config = jlib.ConfigHelper()
    if not config.required_vars_are_set():
        sys.exit(1)

    # Create objects we'll interact with later
    halo = jlib.Halo(config.halo_api_key, config.halo_api_secret_key,
                     config.halo_api_hostname, config.describe_issues_threads)

    # Get issues created, changed, deleted since starting timestamp
    msg = "Getting all Halo issues since {}".format(config.tstamp)  # NOQA
    logger.info(msg)

    issues_filters = {"no_sva": config.no_sva}
    halo_issues = halo.describe_all_issues(config.tstamp, config.critical_only,
                                           **issues_filters)

    # Print initial stats
    jlib.Utility.print_initial_job_stats(config.tstamp, halo_issues)

    # Bail here if there are no issues to process.
    if not halo_issues:
        logger.info("No issues to process!")
        if config.state_manager:
            config.state_manager.set_timestamp(starting_timestamp)
        sys.exit(0)

    # Compare Halo issue IDs against existing Jira issues, to determine
    # what should be created, updated, closed, or reopened.
    msg = "Getting Jira issues which correspond to Halo issues."
    logger.info(msg)
    marching_orders = jlib.Utility.get_marching_orders(config, halo_issues)

    # Reconcile.
    jlib.Reconciler.reconcile_marching_orders(config, marching_orders)

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
