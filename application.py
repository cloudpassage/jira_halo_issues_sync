#!/usr/bin/python3
import boto3
import datetime
import jlib
import json
import os
import sys
import binascii
from base64 import b64decode
from itertools import groupby
from concurrent.futures import ThreadPoolExecutor, as_completed


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

    for rule in config.rules:
        halo_issues = halo.describe_all_issues(config.tstamp, rule["filters"])
        # Print initial stats
        jlib.Utility.print_initial_job_stats(config.tstamp, halo_issues)

        # Bail here if there are no issues to process.
        if not halo_issues:
            logger.info("No issues to process!")

        # Compare Halo issue IDs against existing Jira issues, to determine
        # what should be created, updated, closed, or reopened.
        msg = "Getting Jira issues which correspond to Halo issues."
        logger.info(msg)

        groupby_params = rule.get("groupby", [])
        pool = ThreadPoolExecutor(max_workers=7)
        marching_orders_futures = {}
        for group_key, issues_group in groupby(halo_issues, key=lambda issue: {x: issue[x] for x in groupby_params}):
            for project_key in rule['jira_config']['project_keys']:
                args = (config, rule, project_key, group_key)
                marching_orders_futures[pool.submit(jlib.Utility.get_marching_orders, list(issues_group), *args)] = args
        issues_count = 0
        for future in as_completed(marching_orders_futures):
            # Reconcile.
            args = marching_orders_futures[future]
            marching_orders = future.result()
            print(marching_orders)
            issues_count += len(marching_orders.keys())
            jlib.Reconciler.reconcile_marching_orders(marching_orders, *args)

    logger.info("Done!")
    if not issues_count:
        if config.state_manager:
            config.state_manager.set_timestamp(starting_timestamp)
        else:
            config.write_timestamp_to_file(starting_timestamp)


    return {"result": json.dumps(
                {"message": "Halo/Jira issue sync complete",
                 "total_issues": issues_count})}


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
        except (kms.exceptions.InvalidCiphertextException, binascii.Error) as e:
            msg = "Error decrypting {} with KMS, will try plaintext: {}".format(encrypted_var, e)  # NOQA
            logger.error(msg)
    return main()


if __name__ == "__main__":
    main()
