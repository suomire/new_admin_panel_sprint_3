import logging.config


class LoggerFactory:
    _logger = None

    LOGGER_NAME = "etl_logger"

    def __init__(self):
        logging.config.fileConfig("01_etl/logger.conf", disable_existing_loggers=False)
        self._logger = logging.getLogger(self.LOGGER_NAME)
        self._logger.debug("New logger instance was generated")

    def get_logger(self):
        return self._logger
