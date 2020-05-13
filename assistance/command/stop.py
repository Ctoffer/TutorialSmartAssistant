class StopCommand:
    def __init__(self, printer, function):
        self.printer = printer
        self._function = function

        self._name = "stop"
        self._aliases = ("exit", "finish", "cancel", "terminate")
        self._min_arg_count = 0
        self._max_arg_count = 0

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

    def __call__(self):
        self._function()