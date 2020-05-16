import os
import re
import shutil
from json import dump as json_save

from util.console import single_choice


class WorkflowDownloadCommand:
    def __init__(self, printer, function, moodle):
        self.printer = printer
        self._function = function
        self._moodle = moodle

        self._name = "workflow.download"
        self._aliases = ("w.down",)
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


class WorkflowUnzipCommand:
    def __init__(self, printer, storage):
        self.printer = printer
        self._storage = storage

        from py7zr import unpack_7zarchive
        shutil.register_unpack_format('7zip', ['.7z'], unpack_7zarchive)

        self._name = "workflow.unzip"
        self._aliases = ("w.uz",)
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
            raw_folder = self._storage.get_raw_folder(exercise_number)
            preprocessed_folder = self._storage.get_preprocessed_folder(exercise_number)

            for file in os.listdir(raw_folder):
                if not file.endswith(".json"):
                    if file.endswith(".tar.gz"):
                        extension = ".tar.gz"
                        file_name = file[:len(extension)]
                    else:
                        file_name, extension = os.path.splitext(file)

                    try:
                        source_path = os.path.join(raw_folder, file)
                        normalized_name, problems = self._normalize_file_name(file_name, exercise_number)
                        target_path = os.path.join(preprocessed_folder, normalized_name)

                        if not extension.endswith("zip"):
                            problems.append(f"Minor: Wrong archive format, please use '.zip' instead of '{extension}'.")

                        self.printer.inform(f"Unpacking {file} ... ", end="")
                        if len(problems) > 0:
                            self.printer.inform()
                            self.printer.warning("While normalizing name there were some problems:")
                            self.printer.indent()
                            for problem in problems:
                                self.printer.warning("- " + problem)
                            self.printer.outdent()

                        shutil.unpack_archive(source_path, target_path)
                        self.printer.confirm("[OK]")

                        with open(os.path.join(target_path, "submission_meta.json"), 'w', encoding='utf-8') as fp:
                            data = {
                                "original_name": file,
                                "problems": problems
                            }
                            json_save(data, fp)

                    except shutil.ReadError:
                        self.printer.error(f"Not supported archive-format: '{extension}'")

        except ValueError:
            self.printer.error(f"Exercise number must be an integer, not '{args[0]}'")

    def _normalize_file_name(self, file_name, exercise_number):
        problems = list()
        correct_file_name_end = f'_ex{exercise_number:02d}'

        if file_name.endswith(f"-ex{exercise_number:02d}") or file_name.endswith(f"-ex{exercise_number:}"):
            problems.append(f"Used '-' instead of '_' to mark end of filename. Please use '{correct_file_name_end}'")
            file_name = file_name.replace(f'-ex{exercise_number:02d}', correct_file_name_end) \
                .replace(f'-ex{exercise_number:}', correct_file_name_end)

        if correct_file_name_end != f"_ex{exercise_number:}" and file_name.endswith(f"_ex{exercise_number:}"):
            problems.append(f"The exercise number should be formatted with two digits.")
            file_name = file_name.replace(f'_ex{exercise_number:}', correct_file_name_end)

        if not (file_name.endswith(f"_ex{exercise_number:02d}")):
            problems.append(f"Filename does not end with required '{correct_file_name_end}'.")
            file_name += f"_ex{exercise_number:02d}"

        file_name = file_name[:-len(correct_file_name_end)]
        hyphen_score = file_name.count('-')
        underscore_score = file_name.count('_')
        student_names = list()

        if hyphen_score - 1 == underscore_score:
            student_names = list()
            for student_name in file_name.split("_"):
                parts = re.findall(r'[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))', student_name)
                if len(parts) > 0:
                    student_name = ("-".join(parts))

                student_name = student_name.split("-")
                student_name = " ".join(student_name)
                if len(student_name) > 0:
                    student_names.append(student_name)

            students = list()
            for student_name in student_names:
                possible_students = self._storage.get_students_by_name(student_name)
                if len(possible_students) == 0:
                    self.printer.warning(f"Did not find a student matching '{student_name}'.")
                elif len(possible_students) == 1:
                    students.append(possible_students[0])
                else:
                    self.printer.warning(f"Found more then one possible student for '{student_name}'")

            student_names = sorted([student.muesli_name.replace(' ', '-') for student in students])
            if len(student_names) < 2:
                problems.append("Submission groups should consist at least of 2 members!")
            if 3 < len(student_names):
                problems.append("Submission groups should consist at most of 3 members!")

            result = '_'.join(student_names) + correct_file_name_end
        else:
            problem = "Fatal: Wrong naming detected - manuel correction needed."
            problems.append(problem)
            self.printer.error(problem)
            self.printer.error(file_name)
            self.printer.inform()
            self.printer.inform("Please enter the names you can read in the file name.")

            student = self._select_student()
            if student is not None:
                student_names.append(student)
            while self.printer.input("   Are there more students? (y/n): ") == 'y':
                student = self._select_student()
                if student is not None:
                    student_names.append(student)

            result = []
            for student_name in sorted(student_names):
                name_parts = [_ for _ in student_name.split() if len(_) > 0]
                result.append(f'{name_parts[0].replace("-", "")}-{name_parts[-1].replace("-", "")}')

            if len(result) < 2:
                problems.append("Submission groups should consist at least of 2 members!")
            if 3 < len(result):
                problems.append("Submission groups should consist at most of 3 members!")

            result = '_'.join(result) + correct_file_name_end
            problems.append(f"Please use the correct file format! For this submission it would have been '{result}.zip'")

        return result, problems

    def _select_student(self):
        name = self.printer.input(">: ")
        if len(name) == 0:
            return None

        possible_students = self._storage.get_students_by_name(name, mode='my')
        if len(possible_students) == 1:
            return possible_students[0].muesli_name

        elif len(possible_students) == 0:
            self.printer.warning("No match found")
            return None

        else:
            index = single_choice("Please select correct student", possible_students, self.printer)
            return possible_students[index].muesli_name


class WorkflowPrepareCommand:
    def __init__(self, printer, storage, muesli):
        self.printer = printer
        self._storage = storage
        self._muesli = muesli

        self._name = "workflow.prepare"
        self._aliases = ("w.prep",)
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

            preprocessed_folder = self._storage.get_preprocessed_folder(exercise_number)
            working_folder = self._storage.get_working_folder(exercise_number)

            if not os.path.exists(preprocessed_folder):
                self.printer.error(f"The data for exercise {exercise_number} was not preprocessed. "
                                   f"Run workflow.unzip first.")

            if not self._storage.has_exercise_meta(exercise_number):
                self.printer.inform("Meta data for exercise not found. Syncing from MÜSLI ... ", end='')
                self._storage.update_exercise_meta(self._muesli, exercise_number)
                self.printer.confirm("[OK]")

            for directory in os.listdir(preprocessed_folder):
                src_directory = os.path.join(preprocessed_folder, directory)
                target_directory = os.path.join(working_folder, directory)
                if not os.path.exists(target_directory):
                    shutil.copytree(src_directory, target_directory)
                if os.path.isdir(target_directory):
                    self._storage.generate_feedback_template(exercise_number, target_directory, self.printer)
        except ValueError:
            self.printer.error(f"Exercise number must be an integer, not '{args[0]}'")
