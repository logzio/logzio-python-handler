import datetime
import json
import logging
import logging.handlers
import traceback
import sys

from .sender import LogzioSender


class LogzioHandler(logging.Handler):

    def __init__(self, token, logzio_type="python", logs_drain_timeout=3,
                 url="https://listener.logz.io:8071", debug=False):

        if token is "":
            raise Exception("Logz.io Token must be provided")

        self.logzio_type = logzio_type

        self.logzio_sender = LogzioSender(token=token, url=url, logs_drain_timeout=logs_drain_timeout, debug=debug)
        logging.Handler.__init__(self)

    def extra_fields(self, message):

        not_allowed_keys = (
            'args', 'asctime', 'created', 'exc_info', 'stack_info', 'exc_text', 'filename',
            'funcName', 'levelname', 'levelno', 'lineno', 'module',
            'msecs', 'msecs', 'message', 'msg', 'name', 'pathname', 'process',
            'processName', 'relativeCreated', 'thread', 'threadName')

        if sys.version_info < (3, 0):
            var_type = (basestring, bool, dict, float, int, long, list, type(None))
        else:
            var_type = (str, bool, dict, float, int, list, type(None))

        extra_fields = {}

        for key, value in message.__dict__.items():
            if key not in not_allowed_keys:
                if isinstance(value, var_type):
                    extra_fields[key] = value
                else:
                    extra_fields[key] = repr(value)

        return extra_fields

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
        timestamp = now.strftime("%Y-%m-%dT%H:%M:%S") + ".%03d" % (now.microsecond / 1000) + "Z"

        return_json = {
            "logger": message.name,
            "line_number": message.lineno,
            "path_name": message.pathname,
            "log_level": message.levelname,
            "type": self.logzio_type,
            "message": message.getMessage(),
            "@timestamp": timestamp
        }

        if message.exc_info:
            return_json["exception"] = self.format_exception(message.exc_info)
        else:
            formatted_message = self.format(message)

            return_json.update(self.extra_fields(message))

            if isinstance(formatted_message, dict):
                return_json.update(formatted_message)
            else:
                return_json["message"] = formatted_message

        return return_json

    def emit(self, record):
        self.logzio_sender.append(self.format_message(record))
