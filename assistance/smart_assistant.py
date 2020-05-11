from data.storage import InteractiveDataStorage
from moodle.api import MoodleSession
from muesli.api import MuesliSession
from util.console import ConsoleFormatter, string_table


class SmartAssistant:
    def __init__(self):
        self._storage = InteractiveDataStorage()
        self._printer = ConsoleFormatter()
        self._muesli = MuesliSession(account=self._storage.muesli_account)
        self._moodle = MoodleSession(account=self._storage.moodle_account)
        self.ready = True

        self._initialize_connections()
        self._initialize_storage()

    def _initialize_connections(self):
        self._print_header("Initializing Connections")
        self._open_connection_to(self._muesli)
        self._open_connection_to(self._moodle)
        print()

    def _print_header(self, title):
        self._printer.inform('┌' + '─' * 120 + '┐')
        self._printer.inform(f'│{title:^120}│')
        self._printer.inform('└' + '─' * 120 + '┘')

    def _open_connection_to(self, session):
        self._printer.inform(f'Current state: {session.name}')
        if not session.online:
            with self._printer as printer:
                printer.inform("Logging in...", end='')
                try:
                    session.login()
                    printer.confirm("[Success]")
                except ConnectionRefusedError as e:
                    printer.error(f"[Error] - {e}")

    def _initialize_storage(self):
        self._print_header("Initializing Storage")
        self._storage.init_data(self._muesli, self._moodle)
        self._printer.inform()

    def hello(self):
        def my_tutorial_to_str(my_tutorial):
            students = self._storage.get_all_students_of_tutorial(my_tutorial.tutorial_id)
            return f'({my_tutorial.tutorial_id}) ' \
                   f'{my_tutorial.time} {my_tutorial.location:<15}' \
                   f'[{len(students)}]'

        def other_tutorial_to_str(other_tutorial):
            students = self._storage.get_all_students_of_tutorial(other_tutorial.tutorial_id)
            tutor = other_tutorial.tutor.split()
            tutor = f'{tutor[0]} {tutor[-1]}'
            return f'({other_tutorial.tutorial_id}) ' \
                   f'{other_tutorial.time} {other_tutorial.location:<15} ' \
                   f'{tutor:25}' \
                   f'[{len(students)}]'

        self._print_header(f'{"Hello, " + self._storage.my_name_alias:^88}')
        headers = ["My Tutorials", "Other Tutorials"]
        my_tutorials = self._storage.my_tutorials
        my_tutorials = [my_tutorial_to_str(my_tutorial) for my_tutorial in my_tutorials]
        other_tutorials = self._storage.other_tutorials
        other_tutorials = [other_tutorial_to_str(other_tutorial) for other_tutorial in other_tutorials]
        table = string_table(headers, [my_tutorials, other_tutorials])

        with self._printer as printer:
            for line in table:
                printer.inform(line)
        self._printer.inform()

        self._printer.inform("Enter a command or use 'help' / '?' to list all available commands.")
        self._printer.inform()

    def execute_cycle(self):
        command = input(">: ")
        with self._printer as printer:
            printer.inform(f"Entered: {command}")
            if command == "stop":
                self._stop()

    def _stop(self):
        self.ready = False
        self._printer.inform("Close connections ...", end='')
        self._moodle.logout()
        self._muesli.logout()
        self._printer.inform("[OK]")
        self._printer.outdent()
        self._print_header("Have a nice day \\(^_^)/")
