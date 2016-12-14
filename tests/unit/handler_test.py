import ast
import unittest
import logging
import sys
import re
import os
from logzio.handler import LogzioHandler

def dummy_drain_messages():
    pass

class TestHandler(unittest.TestCase):
    def setUp(self):
        self.handler = LogzioHandler('moo')
        self.handler.drain_messages = dummy_drain_messages;

    def test_json(self):
        formatter = logging.Formatter(
            '{ "appname":"%(name)s", "functionName":"%(funcName)s", \"lineNo":"%(lineno)d", "severity":"%(levelname)s", "message":"%(message)s"}')
        self.handler.setFormatter(formatter)

        record = logging.LogRecord(
            name='my-logger',
            level=0,
            pathname='handler_test.py',
            lineno=10,
            msg="this is a test: moo.",
            args=[],
            exc_info=None,
            func='test_json'
        )

        formatted_message = self.handler.format_message(record)
        formatted_message["@timestamp"] = None

        self.assertDictEqual(
            formatted_message,
            {
                '@timestamp': None,
                'appname': 'my-logger',
                'functionName': 'test_json',
                'lineNo': '10',
                'line_number': 10,
                'log_level': 'NOTSET',
                'logger': 'my-logger',
                'message': 'this is a test: moo.',
                'path_name': 'handler_test.py',
                'severity': 'NOTSET',
                'type': 'python'
            }
        )

    def test_string(self):
        record = logging.LogRecord(
            name='my-logger',
            level=0,
            pathname='handler_test.py',
            lineno=10,
            msg="this is a test: moo.",
            args=[],
            exc_info=None,
            func='test_json'
        )

        formatted_message = self.handler.format_message(record)
        formatted_message["@timestamp"] = None

        self.assertDictEqual(
            formatted_message,
            {
                '@timestamp': None,
                'line_number': 10,
                'log_level': 'NOTSET',
                'logger': 'my-logger',
                'message': 'this is a test: moo.',
                'path_name': 'handler_test.py',
                'type': 'python'
             }
        )

    def test_exc(self):
        exc_info = None
        try:
            raise ValueError("oops.")
        except:
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name='my-logger',
            level=0,
            pathname='handler_test.py',
            lineno=10,
            msg="this is a test: moo.",
            args=[],
            exc_info=exc_info,
            func='test_json'
        )

        formatted_message = self.handler.format_message(record)
        formatted_message["@timestamp"] = None

        formatted_message["message"] = formatted_message["message"].replace(os.path.abspath(__file__), "")
        formatted_message["message"] = re.sub(r", line \d+", "", formatted_message["message"])

        self.assertDictEqual(
            {
                '@timestamp': None,
                'line_number': 10,
                'log_level': 'NOTSET',
                'logger': 'my-logger',
                'message': 'Traceback (most recent call last):\n\n  File "", in test_exc\n    raise ValueError("oops.")\n\nValueError: oops.\n',
                'path_name': 'handler_test.py',
                'type': 'python'
            },
            formatted_message
        )

if __name__ == '__main__':
    unittest.main()
