# This class is responsible for handling all asynchronous Logz.io's communication
import sys
import requests
import json
from threading import Thread, enumerate
from datetime import datetime
from time import sleep

if sys.version[0] == '2':
    import Queue as queue
else:
    import queue as queue

MAX_BULK_SIZE_IN_BYTES = 3 * 1024 * 1024  # 3 MB


def backup_logs(logs):
    timestamp = datetime.now().strftime("%d%m%Y-%H%M%S")
    print("Backing up your logs to logzio-failures-{0}.txt".format(timestamp))
    with open("logzio-failures-{0}.txt".format(timestamp), "a") as f:
        f.writelines('\n'.join(logs))


class LogzioSender:
    def __init__(self, token, url="https://listener.logz.io:8071", logs_drain_timeout=5, debug=False):
        self.token = token
        self.url = "{0}/?token={1}".format(url, token)
        self.logs_drain_timeout = logs_drain_timeout
        self.debug = debug

        # Function to see if the main thread is alive
        self.is_main_thread_active = lambda: any((i.name == "MainThread") and i.is_alive() for i in enumerate())

        # Create a queue to hold logs
        self.queue = queue.Queue()

        self.sending_thread = Thread(target=self._drain_queue)
        self.sending_thread.daemon = False
        self.sending_thread.name = "logzio-sending-thread"
        self.sending_thread.start()

    def append(self, logs_message):
        # Queue lib is thread safe, no issue here
        self.queue.put(json.dumps(logs_message))

    def _debug(self, message):
        if self.debug:
            print(str(message))

    def _drain_queue(self):
        last_try = False

        while not last_try:
            # If main is exited, we should run one last time and try to remove all logs
            if not self.is_main_thread_active():
                self._debug("Identified quit of main thread, sending logs one last time")
                last_try = True

            try:
                # Sending logs until queue is empty
                while not self.queue.empty():
                    logs_list = self._get_messages_up_to_max_allowed_size()
                    self._debug("Starting to drain " + str(len(logs_list)) + " logs to Logz.io")

                    # Not configurable from the outside
                    sleep_between_retries = 2
                    number_of_retries = 4

                    should_backup_to_disk = True
                    headers = {"Content-type": "text/plain"}

                    for current_try in range(number_of_retries):
                        should_retry = False
                        try:
                            response = requests.post(self.url, headers=headers, data='\n'.join(logs_list))
                            if response.status_code != 200:
                                if response.status_code == 400:
                                    print("Got 400 code from Logz.io. This means that some of your logs are too big, or badly formatted. response: {0}".format(response.text))
                                    should_backup_to_disk = False
                                    break

                                if response.status_code == 401:
                                    print("You are not authorized with Logz.io! Token OK? dropping logs...")
                                    should_backup_to_disk = False
                                    break
                                else:
                                    print("Got {} while sending logs to Logz.io, Try ({}/{}). Response: {}".format(response.status_code, current_try + 1, number_of_retries, response.text))
                                    should_retry = True
                            else:
                                self._debug("Successfully sent bulk of " + str(len(logs_list)) + " logs to Logz.io!")
                                should_backup_to_disk = False
                                break

                        except Exception as e:
                            print("Got exception while sending logs to Logz.io, Try ({}/{}). Message: {}".format(current_try + 1, number_of_retries, e))
                            should_retry = True

                        if should_retry:
                            sleep(sleep_between_retries)
                            sleep_between_retries *= 2

                    if should_backup_to_disk:
                        # Write to file
                        print("Could not send logs to Logz.io after " + str(number_of_retries) + " tries, backing up to local file system.")
                        backup_logs(logs_list)

            except Exception as e:
                self._debug("Unexpected exception while draining queue to Logz.io, swallowing. Exception: " + str(e))

            if not last_try:
                sleep(self.logs_drain_timeout)

    def _get_messages_up_to_max_allowed_size(self):
        logs_list = []
        while not self.queue.empty():
            logs_list.append(self.queue.get())
            if sys.getsizeof(logs_list) >= MAX_BULK_SIZE_IN_BYTES:
                break
        return logs_list
