import os


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def colored_string(message, color):
    colors = {'red':124, 'orange':202, 'green':40}
    if type(color) == str:
        color = colors[color]

    return f'\033[38;5;{color}m{message}\033[0m'


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
        print(self.indentation + colored_string(message, 'green'), end=end)

    def warning(self, warning, end='\n'):
        print(self.indentation + colored_string(warning, 'orange'), end=end)

    def error(self, error, end='\n'):
        print(self.indentation + colored_string(error, 'red'), end=end)

    def __enter__(self):
        self.indent()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.outdent()

def string_table(header, columns, align_header='^', align_row='>'):
    def pad_entry(entry, size, align):
        return ("{:" + f'{align}{size}' + "}").format(entry)

    def get_or_default(li, index, default=' '):
        if 0 <= index < len(li):
            return li[index]
        else:
            return default

    if len(header) != len(columns):
        raise ValueError('Need the same amount of columns than headers!')

    columns = [[str(entry) for entry in column] for column in columns]
    max_width = [0] * len(header)
    for i, column in enumerate(columns):
        if len(column) == 0:
            max_width[i] = len(header[i])
        else:
            max_width[i] = max(len(header[i]), *[len(_) for _ in column])

    table = list()
    table.append(' │ '.join([pad_entry(entry, max_width[i], align_header) for i, entry in enumerate(header)]))
    table.append('─┼─'.join(['─'* max_width[i] for i in range(len(header))]))
    for col_index in range(max(map(len, columns))):
        table.append(' │ '.join([pad_entry(get_or_default(columns[i], col_index), max_width[i], align_row) for i in range(len(header))]))

    return table
