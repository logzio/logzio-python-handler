import sys
import json
import logging
import datetime
import traceback
import logging.handlers

from .sender import LogzioSender
from .exceptions import LogzioException


class LogzioHandler(logging.Handler):

    def __init__(self,
                 token,
                 logzio_type="python",
                 logs_drain_timeout=3,
                 url="https://listener.logz.io:8071",
                 debug=False):

        if not token:
            raise LogzioException('Logz.io Token must be provided')

        self.logzio_type = logzio_type

        self.logzio_sender = LogzioSender(
            token=token,
            url=url,
            logs_drain_timeout=logs_drain_timeout,
            debug=debug)
        logging.Handler.__init__(self)

    def extra_fields(self, message):

        not_allowed_keys = (
            'args', 'asctime', 'created', 'exc_info', 'stack_info', 'exc_text',
            'filename', 'funcName', 'levelname', 'levelno', 'lineno', 'module',
            'msecs', 'msecs', 'message', 'msg', 'name', 'pathname', 'process',
            'processName', 'relativeCreated', 'thread', 'threadName')

        return self._extra_fields_handle_dictionary(message, not_allowed_keys)

    @classmethod
    def _extra_fields_recursive(cls, obj, not_allowed_keys=()):
        if sys.version_info < (3, 0):
            # long and basestring don't exist in py3 so, NOQA
            var_type = (basestring, bool, float,  # NOQA
                        int, long, type(None))  # NOQA
        else:
            var_type = (str, bool, dict, float, int, list, type(None))

        if isinstance(obj, (list, tuple)):
            return tuple(cls._extra_fields_recursive(item) for item in obj)
        elif isinstance(obj, dict):
            return cls._extra_fields_handle_dictionary(obj, not_allowed_keys)
        elif isinstance(obj, var_type):
            return obj
        else:
            return repr(obj)

    @classmethod
    def _extra_fields_handle_dictionary(cls, obj, not_allowed_keys=()):
        return {cls._extra_fields_recursive(key): cls._extra_fields_recursive(value)
                for key, value in obj.__dict__.items()
                if key not in not_allowed_keys}

    def flush(self):
        self.logzio_sender.flush()

    def format(self, record):
        message = super(LogzioHandler, self).format(record)
        try:
            return json.loads(message)
        except (TypeError, ValueError):
            return message

    def format_exception(self, exc_info):
        return '\n'.join(traceback.format_exception(*exc_info))

    def format_message(self, message):
        now = datetime.datetime.utcnow()
        timestamp = now.strftime('%Y-%m-%dT%H:%M:%S') + \
            '.%03d' % (now.microsecond / 1000) + 'Z'

        return_json = {
            'logger': message.name,
            'line_number': message.lineno,
            'path_name': message.pathname,
            'log_level': message.levelname,
            'type': self.logzio_type,
            'message': message.getMessage(),
            '@timestamp': timestamp
        }

        if message.exc_info:
            return_json['exception'] = self.format_exception(message.exc_info)

            # We want to ignore default logging formatting on exceptions
            # As we handle those differently directly into exception field
            message.exc_info = None
            message.exc_text = None

        formatted_message = self.format(message)
        if isinstance(formatted_message, dict):
            return_json.update(formatted_message)
        else:
            return_json['message'] = formatted_message

        return_json.update(self.extra_fields(message))
        return return_json

    def emit(self, record):
        self.logzio_sender.append(self.format_message(record))
