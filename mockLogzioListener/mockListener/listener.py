# noinspection PyUnresolvedReferences
import future
import socket

from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from .logsList import logs_list
from .persistentFlags import persistent_flags


class ListenerHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length"))
            all_logs = self.rfile.read(content_length).decode("utf-8").split('\n')
            if len(all_logs) == 0:
                self._set_response(400, "Bad Request", b"Bad request you got there, pal")
                return

            for log in all_logs:
                if log != "":
                    if persistent_flags.get_server_error():
                        self._set_response(500, "Issue!!!!!!!", b"Not good, not good at all.")
                        return

                    logs_list.list.append(log)

            self._set_response(200, "OK", b"Shabam! got logs.")
            return

        except IndexError:
            self._set_response(400, "Bad Request", b"Bad request you got there, pal")
            return

    def _set_response(self, http_code, http_description, byte_body):
        self.send_response(http_code, http_description)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(byte_body)


class MockLogzioListener:
    def __init__(self):
        self.port = _find_available_port()
        self.host = "localhost"

        self.server = HTTPServer((self.host, self.port), ListenerHandler)

        self.listening_thread = Thread(target=self._start_listening)
        self.listening_thread.daemon = True
        self.listening_thread.name = "mock-logzio-listener"
        self.listening_thread.start()
        self.logs_list = logs_list.list
        self.persistent_flags = persistent_flags

    def _start_listening(self):
        self.server.serve_forever()

    def get_port(self):
        return self.port

    def get_host(self):
        return self.host

    def find_log(self, search_log):
        for current_log in self.logs_list:
            if search_log in current_log:
                return True

        return False

    def get_number_of_logs(self):
        return len(self.logs_list)

    def clear_logs_buffer(self):
        self.logs_list[:] = []

    def set_server_error(self):
        self.persistent_flags.set_server_error()

    def clear_server_error(self):
        self.persistent_flags.clear_server_error()


def _find_available_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("", 0))
    sock.listen(1)
    port = sock.getsockname()[1]
    sock.close()
    return port
