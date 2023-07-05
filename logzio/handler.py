import sys
import json
import logging
import datetime
import traceback
import logging.handlers

from .sender import LogzioSender
from .exceptions import LogzioException


class ExtraFieldsLogFilter(logging.Filter):

    def __init__(self, extra: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extra = extra

    def filter(self, record):
        record.__dict__.update(self.extra)
        return True


class LogzioHandler(logging.Handler):

    def __init__(self,
                 token,
                 logzio_type="python",
                 logs_drain_timeout=3,
                 url="https://listener.logz.io:8071",
                 debug=False,
                 backup_logs=True,
                 network_timeout=10.0,
                 retries_no=4,
                 retry_timeout=2,
                 add_context=False):

        if not token:
            raise LogzioException('Logz.io Token must be provided')

        self.logzio_type = logzio_type

        if add_context:
            try:
                from opentelemetry.instrumentation.logging import LoggingInstrumentor
                LoggingInstrumentor().instrument(set_logging_format=True)
            except ImportError:
                print("""Can't add trace context.
OpenTelemetry logging optional package isn't installed.
Please install the following package:
pip install 'logzio-python-handler[opentelemetry-logging]'""")
        self.logzio_sender = LogzioSender(
            token=token,
            url=url,
            logs_drain_timeout=logs_drain_timeout,
            debug=debug,
            backup_logs=backup_logs,
            network_timeout=network_timeout,
            number_of_retries=retries_no,
            retry_timeout=retry_timeout)
        logging.Handler.__init__(self)

    def __del__(self):
        del self.logzio_sender

    def extra_fields(self, message):

        not_allowed_keys = (
            'args', 'asctime', 'created', 'exc_info', 'stack_info', 'exc_text',
            'filename', 'funcName', 'levelname', 'levelno', 'lineno', 'module',
            'msecs', 'msecs', 'message', 'msg', 'name', 'pathname', 'process',
            'processName', 'relativeCreated', 'thread', 'threadName')

        if sys.version_info < (3, 0):
            # long and basestring don't exist in py3 so, NOQA
            var_type = (basestring, bool, dict, float,  # NOQA
                        int, long, list, type(None))  # NOQA
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
            if record.exc_info:
                message = message.split("\n")[0]  # only keep the original formatted message part
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

        # # We want to ignore default logging formatting on exceptions
        # # As we handle those differently directly into exception field

        formatted_message = self.format(message)
        # Exception with multiple fields, apply them to log json.
        if isinstance(formatted_message, dict):
            return_json.update(formatted_message)
        # No exception, apply default formatted message
        elif not message.exc_info:
            return_json['message'] = formatted_message

        return_json.update(self.extra_fields(message))
        return return_json

    def emit(self, record):
        self.logzio_sender.append(self.format_message(record))
