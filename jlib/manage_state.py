import os

import boto3
from botocore.exceptions import ClientError

from .logger import Logger


class ManageState(object):
    """All state (timestamp) management happens in this class.

    We expect to see the `AWS_REGION` environment variable set. This is
    required for AWS API interaction, and if it is not present, initialization
    will raise a ValueError.

    Args:
        ssm_param_name (str): Name for SSM parameter.
        ssm_param_desc (str): Description string for SSM param.
    """
    def __init__(self, ssm_param_name):
        self.region = os.getenv("AWS_REGION")
        if self.region is None:
            msg = ("Missing AWS_REGION environment variable. Cannot manage "
                   "state between invocations.")
            raise ValueError(msg)
        self.client = boto3.client('ssm', region_name=self.region)
        self.param_name = ssm_param_name
        self.logger = Logger()

    def get_timestamp(self):
        """Get the timestamp currrently stored in the SSM parameter."""
        param = self.client.get_parameter(Name=self.param_name)
        timestamp = param['Parameter']['Value']
        return timestamp

    def set_timestamp(self, timestamp):
        """Delete and re-create SSM parameter."""
        try:
            # We do this so that we won't exceed the max param versions
            self.client.delete_parameter(Name=self.param_name)
        except ClientError as e:
            msg = "Exception when attempting to remove timestamp from SSM: {}"
            self.logger.error(msg.format(e))
        response = self.client.put_parameter(Name=self.param_name,
                                             Value=timestamp, Type='String',
                                             Overwrite=True)
        msg = 'Updated timestamp parameter named {} with {} (version {})'
        self.logger.info(msg.format(self.param_name, timestamp,
                                    response['Version']))
        return

    def increment_timestamp(self, timestamp):
        """Only update SSM parameter ()faster than delete/re-create."""
        response = self.client.put_parameter(Name=self.param_name,
                                             Value=timestamp, Type='String',
                                             Overwrite=True)
        msg = 'Updated timestamp parameter named {} with {} (version {})'
        self.logger.info(msg.format(self.param_name, timestamp,
                                    response['Version']))
        return
