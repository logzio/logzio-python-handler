import functools
import logging


class LogzioFlusher(logging.Logger):

    def __init__(self, logger):
        self.logger = logger

    def __call__(self, function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except Exception as e:
                self.logger.exception('call failed: {}'.format(e))
                raise
            finally:
                [h.flush() for h in self.logger.root.handlers]
        return wrapper
