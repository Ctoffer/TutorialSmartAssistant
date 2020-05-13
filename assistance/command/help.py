from util.console import string_table


class HelpCommand:
    def __init__(self, printer, register):
        self.printer = printer
        self._register = register

        self._name = "help"
        self._aliases = ("?",)
        self._min_arg_count = 0
        self._max_arg_count = 1

    @property
    def name(self):
        return self._name

    @property
    def aliases(self):
        return self._aliases

    @property
    def min_arg_count(self):
        return self._min_arg_count

    @property
    def max_arg_count(self):
        return self._max_arg_count

    @property
    def help(self):
        return "No help available"

    def __call__(self, *args):
        if len(args) == 0:
            self._print_all_commands()
        elif len(args) == 1:
            self._print_single_command(args[0])
        else:
            self.printer.error(f"Expected no or one argument, not {len(args)}")

    def _print_all_commands(self):
        commands = sorted(self._register.commands, key=lambda cmd: cmd.name)
        header = ["Name", "Aliases", "Description"]
        columns = [list()] * len(header)
        columns[0] = [cmd.name for cmd in commands]
        columns[1] = [" ".join([f"'{alias}'" for alias in cmd.aliases]) for cmd in commands]
        columns[2] = [cmd.help.split("\n")[0] for cmd in commands]

        for line in string_table(header, columns):
            self.printer.inform(line)

    def _print_single_command(self, command):
        for line in self._register.get_command(command).help.split("\n"):
            self.printer.inform(line)