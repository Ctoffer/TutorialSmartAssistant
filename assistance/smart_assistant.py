from data.storage import InteractiveDataStorage
from moodle.api import MoodleSession
from muesli.api import MuesliSession
from util.console import ConsoleFormatter


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
        self._printer.inform('┌' + '─' * 88 + '┐')
        self._printer.inform(f'│{title:^88}│')
        self._printer.inform('└' + '─' * 88 + '┘')

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
        self._print_header(f'{"Hello, " + self._storage.my_name_alias:^88}')
        my_tutorials = self._storage.my_tutorials
        for my_tutorial in my_tutorials:
            students = self._storage.get_all_students_of_tutorial(my_tutorial.tutorial_id)
            self._printer.inform(f'{my_tutorial.time} {my_tutorial.location} [{len(students)}]')
        self._printer.inform()

        self._printer.inform("Enter a command or use 'help' / '?' to list all available commands.")
        self._printer.inform()

    def execute_cycle(self):
        command = input(">: ")
        with self._printer as printer:
            printer.inform(f"Entered: {command}")
