import logging
import logging.handlers
import requests
import traceback
import datetime
import json

from threading import Event, Thread, Condition, Lock, enumerate
from time import sleep


class LogzioHandler(logging.Handler):

    # Hold all logs buffered
    logs = []

    # Event for locking buffer additions while draining
    buffer_event = Event()

    # Condition to count log messages
    logs_counter_condition = Condition()

    # Lock to only drain logs once
    drain_lock = Lock()

    def __init__(self, token, logs_drain_count=100, logs_drain_timeout=10,
                 logzio_type="python", url="https://listener.logz.io:8071/"):

        if token is "":
            raise Exception("Logz.io Token must be provided")

        logging.Handler.__init__(self)
        self.logs_drain_count = logs_drain_count
        self.logs_drain_timeout = logs_drain_timeout
        self.logzio_type = logzio_type
        self.url = "{0}?token={1}".format(url, token)

        self.is_main_thread_active = lambda: any((i.name == "MainThread") and i.is_alive() for i in enumerate())

        self.buffer_event.set()

        # Create threads
        timeout_thread = Thread(target=self.wait_to_timeout_and_drain)
        counter_thread = Thread(target=self.count_logs_and_drain)

        # And start them
        timeout_thread.start()
        counter_thread.start()

    def wait_to_timeout_and_drain(self):

        while True:
            sleep(self.logs_drain_timeout)
            if len(self.logs) > 0:
                self.drain_messages()

            if not self.is_main_thread_active():
                # Signal the counter thread so it would exit as well
                try:
                    self.logs_counter_condition.acquire()
                    self.logs_counter_condition.notify()
                finally:
                    self.logs_counter_condition.release()
                    break

    def count_logs_and_drain(self):
        try:
            # Acquire the condition
            self.logs_counter_condition.acquire()

            # Running indefinite
            while True:

                # Waiting for new log lines to come
                self.logs_counter_condition.wait()

                if not self.is_main_thread_active():
                    break

                # Do we have enough logs to drain?
                if len(self.logs) >= self.logs_drain_count:
                    self.drain_messages()

        finally:
            self.logs_counter_condition.release()

    def add_to_buffer(self, message):

        # Check if we are currently draining buffer so we wont loose logs
        self.buffer_event.wait()

        try:
            # Acquire the condition
            self.logs_counter_condition.acquire()
            self.logs.append(json.dumps(message))

            # Notify watcher for a new log coming in
            self.logs_counter_condition.notify()

        finally:
            # Release the condition
            self.logs_counter_condition.release()

    def handle_exceptions(self, message):
        if message.exc_info:
            return '\n'.join(traceback.format_exception(*message.exc_info))
        else:
            return message.getMessage()

    def format_message(self, message):

        message_field = self.handle_exceptions(message)
        now = datetime.datetime.utcnow()
        timestamp = now.strftime("%Y-%m-%dT%H:%M:%S") + ".%03d" % (now.microsecond / 1000) + "Z"

        return_json = {
            "logger": message.name,
            "line_number": message.lineno,
            "path_name": message.pathname,
            "log_level": message.levelname,
            "message": message_field,
            "type": self.logzio_type,
            "@timestamp": timestamp
        }

        return return_json

    def drain_messages(self):
        try:
            self.buffer_event.clear()
            self.drain_lock.acquire()

            # Not configurable from the outside
            sleep_between_retries = 2000
            number_of_retries = 4

            success_in_send = False
            headers = {"Content-type": "text/plain"}

            for current_try in range(number_of_retries):
                response = requests.post(self.url, headers=headers, data='\n'.join(self.logs))

                if response.status_code != 200:
                    sleep(sleep_between_retries)
                    sleep_between_retries *= 2
                else:
                    success_in_send = True
                    break

            if success_in_send:  # Only clear the logs from the buffer if we managed to send them
                # Clear the buffer
                self.logs = []

        finally:
            self.buffer_event.set()
            self.drain_lock.release()

    def emit(self, record):
        self.add_to_buffer(self.format_message(record))


