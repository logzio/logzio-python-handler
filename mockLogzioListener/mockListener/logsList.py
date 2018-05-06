# Modules imported only once, this is effectively a singleton


class LogsList:
    def __init__(self):
        self.list = []


logs_list = LogsList()
