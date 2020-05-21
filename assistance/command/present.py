from assistance.command.info import select_student_by_name


class PresentCommand:
    def __init__(self, printer, storage, muesli):
        self.printer = printer
        self._storage = storage
        self._muesli = muesli

        self._name = "presented"
        self._aliases = ("pres", "[x]")
        self._min_arg_count = 1
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
        return "No help available."

    def __call__(self, *args):
        if not self._storage.muesli_data.presentation.supports_presentations:
            self.printer.error("Presenting is not supported. Please change config.json if you want to enable it.")
        else:
            name = args[0]
            select_student_by_name(
                name,
                self._storage,
                self.printer,
                self._update_presented_in_muesli,
                mode='my'
            )

    def _update_presented_in_muesli(self, student):
        self._muesli.update_presented(student, self._storage.muesli_data.presentation.name, self.printer)