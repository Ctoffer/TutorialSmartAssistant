import os


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def colored_string(message, color):
    colors = {'red': 124, 'orange': 202, 'green': 40}
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
        print(f"{self.indentation}{message}", end=end)

    def confirm(self, message, end='\n'):
        print(f"{self.indentation}{colored_string(message, 'green')}", end=end)

    def warning(self, warning, end='\n'):
        print(f"{self.indentation}{colored_string(warning, 'orange')}", end=end)

    def error(self, error, end='\n'):
        print(f"{self.indentation}{colored_string(error, 'red')}", end=end)

    def input(self, message=""):
        return input(f"{self.indentation}{message}")

    def ask(self, question):
        self.inform(question)
        answer = self.input(">: ")
        return answer

    def __enter__(self):
        self.indent()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.outdent()


def string_framed_line(title, length=120, orientation='^', style='-'):
    lines = list()
    length -= 2
    if style == '=':
        lines.append('╔' + '═' * length + '╗')
        lines.append(('║ {:' + f'{orientation}{length - 2}' + '} ║').format(title))
        lines.append('╚' + '═' * length + '╝')
    elif style == '-':
        lines.append('┌' + '─' * length + '┐')
        lines.append(('│ {:' + f'{orientation}{length - 2}' + '} │').format(title))
        lines.append('└' + '─' * length + '┘')
    else:
        raise ValueError(f"Unknown frame style '{style}' (console.py: string_framed_line)")
    return lines


def print_header(title, printer, length=122, orientation='^'):
    for line in string_framed_line(title, length, orientation, style='='):
        printer.inform(line)


def string_card(title, entries, length=60, title_orientation='<'):
    def normalize_entry(e, max_length):
        e = str(e)
        if len(e) > max_length:
            e = e[:max_length - 4] + "..."
        return e

    lines = list()

    lines.append('┌' + '─' * (length - 2) + '┐')
    lines.append(('│ {:' + f'{title_orientation}{length - 4}' + '} │').format(title))
    lines.append('├' + '─' * (length - 2) + '┤')

    entries = {normalize_entry(k, 32): v for k, v in entries.items()}

    longest_entry_name = max([len(str(_)) for _ in entries])
    space_for_entry_content = length - 2 - longest_entry_name - 2 - 2

    for k, v in entries.items():
        entry = normalize_entry(v, space_for_entry_content)
        lines.append((f'│ {{:<{longest_entry_name}}}: ' + f'{{:<{space_for_entry_content}}} │').format(k, entry))

    lines.append('└' + '─' * (length - 2) + '┘')
    return lines


def align_horizontal(lines_left: list, lines_right, space_size=0):
    def get_or_else(li, idx, default=""):
        try:
            return li[idx]
        except IndexError:
            return default

    result = list()
    space = " " * space_size
    longest_word_left = max([len(_) for _ in lines_left])
    longest_word_right = max([len(_) for _ in lines_right])

    for i in range(max(len(lines_left), len(lines_right))):
        left_word = get_or_else(lines_left, i)
        right_word = get_or_else(lines_right, i)
        format_string = f'{{:<{longest_word_left}}}{{}}{{:>{longest_word_right}}}'
        result.append(format_string.format(left_word, space, right_word))

    return result


def align_vertical(lines_top: list, lines_bottom, space_size=0, alignment='<'):
    result = list()
    longest_word_top = max([len(_) for _ in lines_top])
    longest_word_bottom = max([len(_) for _ in lines_bottom])
    longest_word = max(longest_word_top, longest_word_bottom)

    format_string = f'{{:{alignment}{longest_word}}}'
    for line in lines_top:
        result.append(format_string.format(line))

    for _ in range(space_size):
        result.append(" " * longest_word)

    for line in lines_bottom:
        result.append(format_string.format(line))

    return result


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
    table.append('─┼─'.join(['─' * max_width[i] for i in range(len(header))]))
    for col_index in range(max(map(len, columns))):
        table.append(' │ '.join(
            [pad_entry(get_or_default(columns[i], col_index), max_width[i], align_row) for i in range(len(header))]))

    return table


def single_choice(title, options, printer):
    printer.inform(title)
    for i, option in enumerate(options):
        printer.inform(f'   {i:2d}: {option}')
    printer.inform()
    printer.inform("Enter index to confirm your choice or 'cancel' to cancel the input.")

    while True:
        answer = printer.input(">: ")
        if answer == 'cancel':
            answer = None
            break
        try:
            answer = int(answer)
            if answer < 0:
                with printer:
                    printer.warning("Only positive indices are allowed. Try again or type 'cancel'.")
            else:
                break
        except ValueError:
            with printer:
                printer.warning("Please enter an integer number. Try again or type 'cancel'.")

    return answer
