# Modules imported only once, this is effectively a singleton


class PersistentFlags:

    def __init__(self):
        self.server_error = False

    def set_server_error(self):
        self.server_error = True

    def clear_server_error(self):
        self.server_error = False

    def get_server_error(self):
        return self.server_error

persistent_flags = PersistentFlags()
