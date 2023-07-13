import fnmatch
import logging.config
import os
import time
import json
from unittest import TestCase
from logzio.handler import ExtraFieldsLogFilter
from .mockLogzioListener import listener


def _find(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))

        break  # Not descending recursively
    return result


class TestExtraFieldsFilter(TestCase):

    def setUp(self):
        self.logzio_listener = listener.MockLogzioListener()
        self.logzio_listener.clear_logs_buffer()
        self.logzio_listener.clear_server_error()
        self.logs_drain_timeout = 1
        self.retries_no = 4
        self.retry_timeout = 2
        self.add_context = True
        logging_configuration = {
            "version": 1,
            "formatters": {
                "logzio": {
                    "format": '{"key": "value"}',
                    "validate": False
                }
            },
            "handlers": {
                "LogzioHandler": {
                    "class": "logzio.handler.LogzioHandler",
                    "formatter": "logzio",
                    "level": "DEBUG",
                    "token": "token",
                    'logzio_type': "type",
                    'logs_drain_timeout': self.logs_drain_timeout,
                    'url': "http://" + self.logzio_listener.get_host() + ":" + str(self.logzio_listener.get_port()),
                    'debug': True,
                    'retries_no': self.retries_no,
                    'retry_timeout': self.retry_timeout,
                    'add_context': self.add_context
                }
            },
            "loggers": {
                "test": {
                    "handlers": ["LogzioHandler"],
                    "level": "DEBUG"
                }
            }
        }

        logging.config.dictConfig(logging_configuration)
        self.logger = logging.getLogger('test')

        for curr_file in _find("logzio-failures-*.txt", "."):
            os.remove(curr_file)

    def test_add_extra_fields(self):
        extra_fields = {"foo": "bar"}
        self.logger.addFilter(ExtraFieldsLogFilter(extra=extra_fields))
        log_message = "this log should have a additional fields"
        self.logger.info(log_message)
        time.sleep(self.logs_drain_timeout * 2)
        logs_list = self.logzio_listener.logs_list
        for current_log in logs_list:
            if log_message in current_log:
                log_dict = json.loads(current_log)
                try:
                    self.assertEqual(extra_fields, {**extra_fields, **log_dict})
                except AssertionError as err:
                    print(err)

    def test_remove_extra_fields(self):
        extra_fields = {"foo": "bar"}

        self.logger.addFilter(ExtraFieldsLogFilter(extra=extra_fields))
        log_message = "this log should have a additional fields"
        self.logger.info(log_message)

        self.logger.removeFilter(ExtraFieldsLogFilter(extra=extra_fields))
        unfiltered_log_message = "this log shouldn't have a additional fields"
        self.logger.info(unfiltered_log_message)

        time.sleep(self.logs_drain_timeout * 2)
        logs_list = self.logzio_listener.logs_list
        for current_log in logs_list:
            if unfiltered_log_message in current_log:
                log_dict = json.loads(current_log)
                try:
                    self.assertNotEqual(extra_fields, {**extra_fields, **log_dict})
                except AssertionError as err:
                    print(err)

    def test_add_multiple_extra_fields(self):
        extra_fields = {"foo": "bar"}
        self.logger.addFilter(ExtraFieldsLogFilter(extra=extra_fields))
        log_message = "this log should have additional fields"
        self.logger.info(log_message)

        extra_fields = {"counter":1}
        self.logger.addFilter(ExtraFieldsLogFilter(extra=extra_fields))
        filtered_log_message = "this log should have multiple additional fields"
        self.logger.info(filtered_log_message)

        time.sleep(self.logs_drain_timeout * 2)
        logs_list = self.logzio_listener.logs_list
        for current_log in logs_list:
            if log_message in current_log:
                log_dict = json.loads(current_log)
                try:
                    self.assertEqual(extra_fields, {**extra_fields, **log_dict})
                except AssertionError as err:
                    print(err)
            elif filtered_log_message in current_log:
                log_dict = json.loads(current_log)
                try:
                    self.assertEqual(extra_fields, {**extra_fields, **log_dict})
                except AssertionError as err:
                    print(err)


if __name__ == '__main__':
    unittest.main()
