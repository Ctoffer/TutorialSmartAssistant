from assistance.command.info import select_student_by_name
from data.storage import InteractiveDataStorage


class ImportCommand:
    def __init__(self, printer, storage: InteractiveDataStorage):
        self.printer = printer
        self._storage = storage

        self._name = "import"
        self._aliases = ("<-",)
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

    def __call__(self, *args, **kwargs):
        value = args[0]
        student = select_student_by_name(
            value,
            self._storage,
            self.printer,
            self._storage.import_student,
            mode='other'
        )

        if student is not None:
            tutorial = self._storage.get_tutorial_by_id(student.tutorial_id)
            self.printer.inform(f"The student '{student}' from {tutorial.time} was imported.")
            self.printer.inform(f"Workflow commands will also consider this student now as your own.")


class ExportCommand:
    def __init__(self, printer, storage: InteractiveDataStorage):
        self.printer = printer
        self._storage = storage

        self._name = "export"
        self._aliases = ("->",)
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

    def __call__(self, *args, **kwargs):
        value = args[0]
        student = select_student_by_name(
            value,
            self._storage,
            self.printer,
            self._storage.export_student,
            mode='my'
        )

        if student is not None:
            tutorial = self._storage.get_tutorial_by_id(student.tutorial_id)
            self.printer.inform(f"The student '{student}' from {tutorial.time} was exported.")
            self.printer.inform(f"Workflow commands will ignore this student.")
