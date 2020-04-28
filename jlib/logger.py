"""Handle all logging here."""
import logging
import os


class Logger(object):
    def __init__(self, **kwargs):
        format = "%(asctime)-15s %(levelname)s %(name)s %(message)s"
        logging.basicConfig(format=format)
        self.logger = logging.getLogger(__name__)
        if "rule" in kwargs:
            rule_name = kwargs["rule"]["name"].split(".")[0]
            logFormatter = logging.Formatter("%(asctime)-15s %(levelname)s %(name)s %(message)s")
            self.logger = logging.getLogger(rule_name)

            logfile_path = self.get_logfile_path(rule_name)
            fileHandler = logging.FileHandler(logfile_path)
            fileHandler.setFormatter(logFormatter)
            self.logger.addHandler(fileHandler)

            consoleHandler = logging.StreamHandler()
            consoleHandler.setFormatter(logFormatter)
            self.logger.addHandler(consoleHandler)

        if os.getenv("DEBUG", "") in ["True", "true"]:
            self.set_debug()
        else:
            self.set_info()

    def get_logfile_path(self, rule_name):
        """Return filename (path) for project log file"""
        if not rule_name:
            return
        here_dir = os.path.abspath(os.path.dirname(__file__))
        log_dir = os.path.join(here_dir, '../log')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        filename = os.path.join(log_dir, f'{rule_name}.log')
        return filename

    def set_debug(self):
        self.logger.setLevel(logging.DEBUG)

    def set_info(self):
        self.logger.setLevel(logging.INFO)

    def critical(self, message):
        self.logger.critical(message)

    def error(self, message):
        self.logger.error(message)

    def warn(self, message):
        self.logger.warning(message)

    def info(self, message):
        self.logger.info(message)

    def debug(self, message):
        self.logger.debug(message)
