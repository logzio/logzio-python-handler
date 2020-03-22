import fnmatch
import logging.config
import os
import time
from unittest import TestCase

from .mockLogzioListener import listener


def _find(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))

        break  # Not descending recursively
    return result


class TestLogzioSender(TestCase):
    def setUp(self):
        self.logzio_listener = listener.MockLogzioListener()
        self.logzio_listener.clear_logs_buffer()
        self.logzio_listener.clear_server_error()
        self.logs_drain_timeout = 1

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
                    'debug': True
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

    def test_simple_log_drain(self):
        log_message = "Test simple log drain"
        self.logger.info(log_message)
        time.sleep(self.logs_drain_timeout * 2)
        self.assertTrue(self.logzio_listener.find_log(log_message))

    def test_multiple_lines_drain(self):
        logs_num = 50
        for counter in range(0, logs_num):
            self.logger.info("Test " + str(counter))
        time.sleep(self.logs_drain_timeout * 2)

        for counter in range(0, logs_num):
            self.logger.info("Test " + str(counter))
        time.sleep(self.logs_drain_timeout * 2)

        self.assertEqual(self.logzio_listener.get_number_of_logs(), logs_num * 2)

    def test_server_failure(self):
        log_message = "Failing log message"
        self.logzio_listener.set_server_error()
        self.logger.info(log_message)

        time.sleep(self.logs_drain_timeout * 2)

        self.assertFalse(self.logzio_listener.find_log(log_message))

        self.logzio_listener.clear_server_error()

        time.sleep(self.logs_drain_timeout * 2 * 4)  # Longer, because of the retry

        self.assertTrue(self.logzio_listener.find_log(log_message))

    def test_local_file_backup(self):
        log_message = "Backup to local filesystem"
        self.logzio_listener.set_server_error()
        self.logger.info(log_message)

        # Make sure no file is present
        self.assertEqual(len(_find("logzio-failures-*.txt", ".")), 0)

        time.sleep(2 * 2 * 2 * 2 * 2)  # All of the retries

        failure_files = _find("logzio-failures-*.txt", ".")
        self.assertEqual(len(failure_files), 1)

        with open(failure_files[0], "r") as f:
            line = f.readline()
            self.assertTrue(log_message in line)

    def test_local_file_backup_disabled(self):
        log_message = "Backup to local filesystem"
        self.logzio_listener.set_server_error()
        self.logger.handlers[0].logzio_sender.backup_logs = False
        self.logger.info(log_message)

        # Make sure no file is present
        self.assertEqual(len(_find("logzio-failures-*.txt", ".")), 0)

        time.sleep(2 * 2 * 2 * 2 * 2)  # All of the retries

        # Make sure no file was created
        self.assertEqual(len(_find("logzio-failures-*.txt", ".")), 0)

    def test_can_send_after_fork(self):
        childpid = os.fork()
        child_log_message = 'logged from child process'
        parent_log_message = 'logged from parent process'

        if childpid == 0:
            # Log from the child process
            self.logger.info(child_log_message)
            time.sleep(self.logs_drain_timeout * 2)
            os._exit(0)
        # Wait for the child process to finish
        os.waitpid(childpid, 0)

        # log from the parent process
        self.logger.info(parent_log_message)
        time.sleep(self.logs_drain_timeout * 2)

        # Ensure listener receive all log messages
        self.assertTrue(self.logzio_listener.find_log(child_log_message))
        self.assertTrue(self.logzio_listener.find_log(parent_log_message))
