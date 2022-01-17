import sys
import logging


def get_logger(debug):
    return __get_logger(debug, __name__)


def get_stdout_logger(debug):
    return __get_logger(debug, __name__ + '_stdout', logging.StreamHandler(sys.stdout))


def __get_logger(debug, name, handler=None):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    if handler:
        logger.addHandler(handler)
    return logger
