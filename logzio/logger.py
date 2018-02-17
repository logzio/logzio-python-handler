import sys
import logging


def get_logger(debug):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.addHandler(logging.StreamHandler(sys.stdout))
    return logger
