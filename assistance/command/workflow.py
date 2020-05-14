class WorkflowDownloadCommand:
    def __init__(self, printer, function, moodle):
        self.printer = printer
        self._function = function
        self._moodle = moodle

        self._name = "workflow.download"
        self._aliases = ("w.down", )
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
        try:
            exercise_number = int(args[0])
            self._function(self._moodle, exercise_number, self.printer)
        except ValueError:
            self.printer.error(f"Exercise number must be an integer, not '{args[0]}'")