import os
import re
import shutil
from collections import defaultdict
from json import dump as json_save
from json import load as j_load
from os.path import join as p_join
from types import SimpleNamespace

from assistance.command.info import select_student_by_name
from mail.mail_out import EMailSender
from util.console import single_choice
from util.feedback import FeedbackPolisher


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

                    self.printer.inform("─" * 100)

        except ValueError:
            self.printer.error(f"Exercise number must be an integer, not '{args[0]}'")

    def _normalize_file_name(self, file_name, exercise_number):
        problems = list()
        correct_file_name_end = f'_ex{exercise_number:02d}'

        file_name = self._suffix_check(
            exercise_number,
            file_name,
            problems,
            correct_file_name_end
        )

        file_name = file_name[:-len(correct_file_name_end)]
        self.printer.inform(f"Finding students of '{file_name}'.")
        hyphen_score = file_name.count('-')
        underscore_score = file_name.count('_')
        student_names = list()

        if hyphen_score - 1 == underscore_score:
            result = self._possible_correct_naming(
                file_name,
                student_names,
                problems,
                correct_file_name_end
            )
        else:
            result = self._definitely_not_correct_naming(
                file_name,
                student_names,
                problems,
                correct_file_name_end
            )

        return result, problems

    def _suffix_check(self, exercise_number, file_name, problems, correct_file_name_end):
        self.printer.inform("Checking file name suffix.")
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

        return file_name

    def _possible_correct_naming(self, file_name, student_names, problems, correct_file_name_end):
        for student_name in file_name.split("_"):
            parts = re.findall(r'[A-Z](?:[a-zöäüß]+|[A-Z]*(?=[A-Z]|$))', student_name)
            if len(parts) > 0:
                student_name = ("-".join(parts))

            student_name = student_name.split("-")
            student_name = " ".join(student_name)
            if len(student_name) > 0:
                student_names.append(student_name)

        students = list()
        needed_manual_help = False
        for student_name in student_names:
            student = select_student_by_name(student_name, self._storage, self.printer, students.append, mode='my')
            if student is None:
                self.printer.error(f"Some error happened processing '{file_name}'")
                self.printer.error(f"Did not find a match for '{student_name}'")
                self.printer.error("Increasing scope ... ")
                student = select_student_by_name(student_name, self._storage, self.printer, students.append,
                                                 mode='all')
                if student is not None:
                    self.printer.inform(f"Found the student - consider to import '{student_name}'")
                else:
                    needed_manual_help = True
                    student = self._manual_student_selection()

                    if student is not None:
                        students.append(student)
                    else:
                        self.printer.error("Manual correction failed!")
        student_names = []

        def to_name(s):
            if type(s) == str:
                return s
            else:
                return s.muesli_name

        for student_name in sorted([to_name(student) for student in students]):
            name_parts = [_ for _ in student_name.split() if len(_) > 0]
            student_names.append(f'{name_parts[0].replace("-", "")}-{name_parts[-1].replace("-", "")}')

        if len(student_names) < 2:
            problems.append("Submission groups should consist at least of 2 members!")
        if 3 < len(student_names):
            problems.append("Submission groups should consist at most of 3 members!")

        result = '_'.join(student_names) + correct_file_name_end
        if needed_manual_help:
            problems.append(
                f"Please use the correct file format! For this submission it would have been '{result}.zip'"
            )

        return result

    def _manual_student_selection(self):
        self.printer.inform("No match found in extended scope - manual correction needed.")
        student = self._select_student(mode='all', return_name=False)
        if student is None:
            self.printer.inform("No student found with entered name. Please try only a name part.")
            student = self._select_student(mode='all', return_name=False)

        while student is None and self.printer.ask("Do you want to try again? (y/n)") == 'y':
            self.printer.inform("No student found with entered name. Please try only a name part.")
            student = self._select_student(mode='all', return_name=False)

        return student

    def _definitely_not_correct_naming(self, file_name, student_names, problems, correct_file_name_end):
        problem = "Fatal: Wrong naming detected - manual correction needed."
        problems.append(problem)
        self.printer.error(problem)
        self.printer.error(file_name)
        self.printer.inform()
        self.printer.inform("Please enter the names you can read in the file name separated with ','.")

        names = self.printer.input(">: ")
        for name in names.split(','):
            student = self._select_student(name=name)
            if student is not None:
                student_names.append(student)
            else:
                while student is None:
                    self.printer.warning(f"Did not find a student with name '{name}'.")
                    self.printer.inform("Please try again.")
                    student = self._select_student()
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

        return result

    def _select_student(self, return_name=True, mode='my', name=None):
        if name is None:
            name = self.printer.input(">: ")

        if len(name) == 0:
            result = None
        else:
            possible_students = self._storage.get_students_by_name(name, mode=mode)
            if len(possible_students) == 1:
                result = possible_students[0]

            elif len(possible_students) == 0:
                self.printer.warning("No match found")
                result = None

            else:
                index = single_choice("Please select correct student", possible_students, self.printer)
                result = possible_students[index]

        if return_name and result is not None:
            return result.muesli_name
        else:
            return result


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

            can_generate_feedback = False
            if not self._storage.has_exercise_meta(exercise_number):
                self.printer.inform("Meta data for exercise not found. Syncing from MÜSLI ... ", end='')
                try:
                    self._storage.update_exercise_meta(self._muesli, exercise_number)
                    can_generate_feedback = True
                    self.printer.confirm("[OK]")
                except TypeError:
                    self.printer.error("[Err]")
                    self.printer.error("No credit stats found for this exercise.")
            else:
                can_generate_feedback = True

            for directory in os.listdir(preprocessed_folder):
                src_directory = os.path.join(preprocessed_folder, directory)
                target_directory = os.path.join(working_folder, directory)
                if not os.path.exists(target_directory):
                    shutil.copytree(src_directory, target_directory)
                if can_generate_feedback and os.path.isdir(target_directory):
                    self._storage.generate_feedback_template(exercise_number, target_directory, self.printer)
        except ValueError:
            self.printer.error(f"Exercise number must be an integer, not '{args[0]}'")


class WorkflowConsolidate:
    def __init__(self, printer, storage):
        self.printer = printer
        self._storage = storage

        self._name = "workflow.consolidate"
        self._aliases = ("w.cons",)
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
        exercise_number = int(args[0])
        working_folder = self._storage.get_working_folder(exercise_number)
        finished_folder = self._storage.get_finished_folder(exercise_number)

        for directory in os.listdir(working_folder):
            self.printer.inform()
            self.printer.inform(f"Working in {directory}")
            self.printer.inform("Polishing feedback ... ", end='')
            polisher = FeedbackPolisher(
                self._storage,
                p_join(working_folder, directory),
                self.printer
            )
            self.printer.confirm("[Ok]")
            self.printer.inform("Saving meta data   ... ", end='')
            polisher.save_meta_to_folder(p_join(finished_folder, directory))
            self.printer.confirm("[Ok]")


class WorkflowUpload:
    def __init__(self, printer, storage, muesli):
        self.printer = printer
        self._storage = storage
        self._muesli = muesli

        self._name = "workflow.upload"
        self._aliases = ("w.up",)
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
        exercise_number = int(args[0])
        finished_folder = self._storage.get_finished_folder(exercise_number)
        meta_file_name = "meta.json"

        data = defaultdict(dict)

        for directory in os.listdir(finished_folder):
            with open(p_join(finished_folder, directory, meta_file_name), 'r', encoding="utf-8") as fp:
                meta = SimpleNamespace(**j_load(fp))
                for muesli_id in meta.muesli_ids:
                    student = self._storage.get_student_by_muesli_id(muesli_id)
                    data[student.tutorial_id][muesli_id] = meta.credits_per_task

        for tutorial_id, student_data in data.items():
            tutorial = self._storage.get_tutorial_by_id(tutorial_id)
            self.printer.inform(
                f"Uploading credits to {tutorial.time} for {len(student_data.keys()):>3d} students ... ",
                end=''
            )
            exercise_id = self._muesli.get_exercise_id(
                tutorial_id,
                self._storage.muesli_data.exercise_prefix,
                exercise_number
            )
            status, number_of_changes = self._muesli.upload_credits(tutorial_id, exercise_id, student_data)

            if status:
                self.printer.confirm("[Ok]", end="")
                self.printer.inform(f" Changed {number_of_changes:>3d} entries.")
            else:
                self.printer.error("[Err]")
                self.printer.error("Please check your connection state.")


class WorkflowSendMail:
    def __init__(self, printer, storage):
        self.printer = printer
        self._storage = storage

        self._name = "workflow.send_feedback"
        self._aliases = ("w.send",)
        self._min_arg_count = 1
        self._max_arg_count = 2

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

    def _parse_arguments(self, args):
        if len(args) == 1:
            exercise_number = int(args[0])
            debug = False
        else:
            if args[0].lower() == '--debug':
                debug = True
                exercise_number = int(args[1])
            else:
                exercise_number = int(args[0])
                debug = args[1].lower() == '--debug'

                if not debug:
                    raise ValueError(f'Unexpected flag {args[1]}')

        return exercise_number, debug

    def __call__(self, *args):
        exercise_number, debug = self._parse_arguments(args)
        if debug:
            self.printer.confirm("Running in debug mode.")

        finished_folder = self._storage.get_finished_folder(exercise_number)
        feedback_file_name = f"{self._storage.muesli_data.feedback.file_name}.txt"
        meta_file_name = "meta.json"

        with EMailSender(self._storage.email_account, self._storage.my_name) as sender:
            for directory in os.listdir(finished_folder):
                students = list()
                with open(p_join(finished_folder, directory, meta_file_name), 'r', encoding="utf-8") as fp:
                    meta = SimpleNamespace(**j_load(fp))

                    for muesli_id in meta.muesli_ids:
                        try:
                            student = self._storage.get_student_by_muesli_id(muesli_id)
                            students.append(student)
                        except ValueError:
                            self.printer.error(f"Did not find student with id {muesli_id}, maybe he left the tutorial?")

                    feedback_path = p_join(finished_folder, directory, feedback_file_name)

                    message = list()
                    message.append("Dieses Feedback ist für:")
                    for student in students:
                        message.append(f"• {student.muesli_name} ({student.muesli_mail})")
                    message.append("")
                    message.append("Das Feedback befindet sich im Anhang.")
                    message.append("")
                    message.append(f"LG {self._storage.my_name_alias}")
                    message = "\n".join(message)

                    student_names = ', '.join([student.muesli_name for student in students])
                    self.printer.inform(f"Sending feedback to {student_names} ... ", end='')
                    try:
                        sender.send_feedback(
                            students,
                            message,
                            feedback_path,
                            self._storage.muesli_data.exercise_prefix,
                            exercise_number,
                            debug=debug
                        )
                        self.printer.confirm("[Ok]")
                    except BaseException as e:
                        self.printer.error(f"[Err] - {e}")

