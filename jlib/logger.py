"""Handle all loging here."""
import logging
import os

class Logger(object):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        format = "%(asctime)-15s %(levelname)s %(name)s %(message)s"
        logging.basicConfig(format=format)
        if os.getenv("DEBUG", "") in ["True", "true"]:
            self.set_debug()
        else:
            self.set_info()

    def set_debug(self):
        self.logger.setLevel(logging.DEBUG)

    def set_info(self):
        self.logger.setLevel(logging.INFO)

    def critical(self, message):
        self.logger.critical(message)

    def error(self, message):
        self.logger.error(message)

    def warn(self, message):
        self.logger.warn(message)

    def info(self, message):
        self.logger.info(message)

    def debug(self, message):
        self.logger.debug(message)
