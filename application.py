#!/usr/bin/python3
import boto3
import datetime
import jlib
import json
import os
import sys
import binascii
from base64 import b64decode


def main():
    logger = jlib.Logger()
    starting_timestamp = datetime.datetime.now().isoformat()
    # Get config
    config = jlib.ConfigHelper()
    if not config.validate_config():
        sys.exit(1)

    # Create objects we'll interact with later
    halo = jlib.Halo(config.halo_api_key, config.halo_api_secret_key, config.halo_api_hostname)
    # Get issues created, changed, deleted since starting timestamp
    logger.info(f"Getting all Halo issues")

    issues_count = 0

    for rule in config.rules:
        halo_issues = halo.get_issues(rule.get("filters", {}))

        # Print initial stats
        logger.info(f"Reconciling {len(halo_issues)} Halo issues")
        reconciler = jlib.Reconciler(config, rule)

        if halo_issues:
            for project_key in rule["jira_config"]["project_keys"]:
                reconciler.reconcile_issues(halo_issues, project_key)

        reconciler.update_all_jira_issues()
        reconciler.cleanup(rule["jira_config"]["project_keys"])

    logger.info("Done!")

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
