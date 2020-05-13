from moodle.api import MoodleSession
from muesli.api import MuesliSession


class ConnectionCommand:
    def __init__(self, printer, moodle, muesli):
        self.printer = printer
        self._moodle: MoodleSession = moodle
        self._muesli: MuesliSession = muesli

        self._name = "connection"
        self._aliases = ("conn",)
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
            self._print_states()
        else:
            argument = args[0]

            if argument in ("--login", "-s"):
                self._login()
            elif argument in ("--state", "-t"):
                self._print_states()
            elif argument in ("--logout", "-T"):
                self._logout()
            else:
                raise ValueError(f"Unknown argument '{argument}'")

    def _login_all(self):
        self._muesli.login()
        self._moodle.login()

    def _login(self, session_name, session):
        self.printer.inform(f'{session_name} login ... ')
        session.login()

    def _print_states(self):
        self._print_state("MÜSLI", self._muesli.get_online_state())
        self._print_state("Moodle", self._moodle.get_online_state())

    def _print_state(self, session_name, state):
        self.printer.inform(f'{session_name}: ', end="")
        if state == "online":
            self.printer.confirm(state)
        elif state == "login required":
            self.printer.warning(state)
        else:
            self.printer.error(state)
