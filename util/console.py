import os


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


class ConsoleFormatter:
    def __init__(self):
        self._indentation_level = 0
        self._buffer = ' ' * 3

    @property
    def indentation(self):
        return self._buffer * self._indentation_level

    def indent(self):
        self._indentation_level += 1

    def outdent(self):
        if self._indentation_level > 0:
            self._indentation_level -= 1

    def inform(self, message='', end='\n'):
        print(self.indentation + message, end=end)

    def confirm(self, message, end='\n'):
        print(self.indentation + '\033[38;5;40m' + message + '\033[0m', end=end)

    def warning(self, warning, end='\n'):
        print(self.indentation + '\033[38;5;202m' + warning + '\033[0m', end=end)

    def error(self, error, end='\n'):
        print(self.indentation + '\033[38;5;124m' + error + '\033[0m', end=end)

    def __enter__(self):
        self.indent()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.outdent()
