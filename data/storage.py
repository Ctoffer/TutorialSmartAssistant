import os
import os.path
from collections import defaultdict
from json import load as j_load, dump as j_dump
from os.path import join as p_join
from time import sleep
from types import SimpleNamespace

import unicodedata

from data.data import Student, Tutorial
from data.student_matching import match_students, print_result_table
from moodle.api import MoodleSession
from muesli.api import MuesliSession
from util.config import load_config


def ensure_folder_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)
    return path


class PhysicalDataStorage:
    def __init__(self, storage_config):
        self._storage_config = storage_config
        self._root = self._storage_config.root
        self._meta_path = ensure_folder_exists(p_join(self._root, "__meta__"))

    def save_my_name(self, my_name):
        path = p_join(self._meta_path, f'01_my_name.json')
        with open(path, 'w') as fp:
            j_dump(my_name, fp, indent=4)

    def load_my_name(self):
        result = None, 'Missing'

        path = p_join(self._meta_path, f'01_my_name.json')
        if os.path.exists(path):
            with open(path, 'r') as fp:
                result = j_load(fp), 'Loaded'

        return result

    def save_tutorial_ids(self, ids, mode='my'):
        path = p_join(self._meta_path, f'02_{mode}_ids.json')
        with open(path, 'w') as fp:
            j_dump(ids, fp, indent=4)

    def load_tutorial_ids(self, mode='my'):
        path = p_join(self._meta_path, f'02_{mode}_ids.json')
        result = list(), "Missing"
        if os.path.exists(path):
            with open(path, 'r') as fp:
                result = j_load(fp), "Loaded"

        return result

    def save_tutorial_data(self, tutorials):
        path = p_join(self._meta_path, f'03_tutorials.json')
        with open(path, 'w') as fp:
            j_dump({k: v.to_json() for k, v in tutorials.items()}, fp, indent=4)

    def load_tutorial_data(self):
        path = p_join(self._meta_path, f'03_tutorials.json')
        result = dict(), "Missing"
        if os.path.exists(path):
            with open(path, 'r') as fp:
                result = {int(k): Tutorial.from_json(v) for k, v in j_load(fp).items()}, "Loaded"

        return result

    def save_students(self, tutorial_id, students):
        directory = ensure_folder_exists(p_join(self._meta_path, "students"))
        path = p_join(directory, f'students_{tutorial_id}.json')
        with open(path, 'w') as fp:
            out_data = [student.to_json_dict() for student in students[tutorial_id]]
            j_dump(out_data, fp, indent=4)

    def load_students(self, tutorial_id):
        directory = ensure_folder_exists(p_join(self._meta_path, "students"))
        path = p_join(directory, f'students_{tutorial_id}.json')
        result = list(), "Missing"
        if os.path.exists(path):
            with open(path, 'r') as fp:
                result = [Student.from_json(student) for student in j_load(fp)], "Loaded"

        return result

    def save_exchanged_students(self, students, mode):
        if mode == 'imported':
            file_name = "imported_students.json"
        elif mode == 'exported':
            file_name = "exported_students.json"
        else:
            raise ValueError(f"Unknown mode '{mode}' (storage.py: save_exchanged_students)")

        directory = ensure_folder_exists(p_join(self._meta_path, "students"))
        path = p_join(directory, file_name)
        with open(path, 'w') as fp:
            j_dump(students, fp, indent=4)

    def load_exchanged_students(self, mode):
        if mode == 'imported':
            file_name = "imported_students.json"
        elif mode == 'exported':
            file_name = "exported_students.json"
        else:
            raise ValueError(f"Unknown mode '{mode}' (storage.py: load_exchanged_students)")

        directory = ensure_folder_exists(p_join(self._meta_path, "students"))
        path = p_join(directory, file_name)
        result = list()

        if os.path.exists(path):
            with open(path, 'r') as fp:
                result = j_load(fp)

        return result


class InteractiveDataStorage:
    __instance = None

    def __new__(cls):
        if InteractiveDataStorage.__instance is None:
            InteractiveDataStorage.__instance = object.__new__(cls)
        InteractiveDataStorage.__instance.my_name = None
        InteractiveDataStorage.__instance.my_name_alias = None
        InteractiveDataStorage.__instance.my_tutorial_ids = list()
        InteractiveDataStorage.__instance.other_tutorial_ids = list()
        InteractiveDataStorage.__instance.tutorials = dict()
        InteractiveDataStorage.__instance.students = dict()
        InteractiveDataStorage.__instance.exported_students = list()
        InteractiveDataStorage.__instance.imported_students = list()
        InteractiveDataStorage.__instance.scores = dict()
        InteractiveDataStorage.__instance.account_data = load_config("account_data.json")
        InteractiveDataStorage.__instance.config = load_config("config.json")
        storage_config = InteractiveDataStorage.__instance.config.storage
        InteractiveDataStorage.__instance.physical_storage = PhysicalDataStorage(storage_config)

        return InteractiveDataStorage.__instance

    def init_data(self, muesli, moodle):
        self._init_my_name(muesli)
        self._init_tutorial_ids(muesli, mode='my')
        self._init_tutorial_ids(muesli, mode='other')
        self._init_tutorials(muesli)
        self._init_students(muesli)
        self._init_moodle_attributes(moodle)

        self.__instance.imported_students = self.physical_storage.load_exchanged_students('imported')
        self.__instance.exported_students = self.physical_storage.load_exchanged_students('exported')

    def _init_my_name(self, muesli: MuesliSession):
        print(f"Load my name ...", end='')
        my_name, state = self.__instance.physical_storage.load_my_name()
        self.my_name = my_name
        print(f'[{state}]')

        if state == "Missing":
            print("Collecting options from MÜSLI...")
            names = muesli.get_tutor_names(self.muesli_data.lecture_id)
            names = sorted(list(names))
            print("Who are you?")
            for i, name in enumerate(names):
                print(f"   {i}: {name}")
            index = None
            while type(index) != int:
                try:
                    index = int(input("Enter your number: "))
                    if index < 0 or len(names) <= index:
                        print(f"Please enter a number between 0 and {len(names) - 1} (borders inclusive).")
                        index = None
                except ValueError:
                    print("Please enter one of the numbers listed above.")

            self.my_name = names[index]
            self.physical_storage.save_my_name(self.my_name)

        self.my_name_alias = self.my_name.split()[0]

    def _init_tutorial_ids(self, muesli: MuesliSession, mode='my'):
        print(f"Load {mode} tutorial ids...", end='')
        ids, state = self.__instance.physical_storage.load_tutorial_ids(mode=mode)
        self._set_tutorial_ids(ids, mode=mode)
        print(f'[{state}]')

        if state == "Missing":
            print("Downloading data from MÜSLI...", end='')
            try:
                self.update_tutorials(muesli, mode=mode)
                print("[OK]")
            except BaseException as e:
                print(f"[ERR] (InteractiveDataStorage: {e})")

    def update_tutorials(self, muesli: MuesliSession, mode="my"):
        if mode == "my":
            tutorials = muesli.get_my_tutorials(self.muesli_data.lecture_id, self.my_name)
            ids = self.my_tutorial_ids
        elif mode == "other":
            tutorials = muesli.get_all_tutorials_of_lecture(self.muesli_data.lecture_id,
                                                            except_ids=self.my_tutorial_ids)
            ids = self.other_tutorial_ids
        else:
            raise ValueError(f"Unknown mode '{mode}'!")

        ids.clear()
        for tutorial in tutorials:
            tid = tutorial.tutorial_id
            self.tutorials[tid] = tutorial
            ids.append(tid)

        self.physical_storage.save_tutorial_ids(ids, mode)
        self.physical_storage.save_tutorial_data(self.tutorials)

    def update_students_of_tutorial(self, muesli: MuesliSession, tutorial_id: int):
        students = muesli.get_all_students_of_tutorial(tutorial_id)
        self.students[tutorial_id] = students
        self.physical_storage.save_students(tutorial_id, self.students)

    def _init_tutorials(self, muesli: MuesliSession):
        print(f"Load tutorial data...", end='')
        tutorials, state = self.physical_storage.load_tutorial_data()
        self.tutorials = tutorials
        print(f'[{state}]')

        if state == "Missing":
            try:
                print("Downloading data from MÜSLI...", end='')
                self.update_tutorials(muesli, 'my')
                self.update_tutorials(muesli, 'other')
                print("[OK]")
            except BaseException as e:
                print(f"[ERR] (InteractiveDataStorage: {e})")

            sleep(2)

    def _init_students(self, muesli: MuesliSession):
        for tutorial_id in self._get_tutorial_ids('my') + self._get_tutorial_ids('other'):
            print(f"Load students of tutorial {tutorial_id}...", end='')
            students, state = self.physical_storage.load_students(tutorial_id)
            self.students[tutorial_id] = students
            print(f'[{state}]')

            if state == "Missing":
                try:
                    print("Downloading data from MÜSLI...", end='')
                    self.update_students_of_tutorial(muesli, tutorial_id)
                    print("[OK]")
                except BaseException as e:
                    print(f"[ERR] (InteractiveDataStorage: {e})")

                sleep(2)

    def _init_moodle_attributes(self, moodle: MoodleSession):
        all_students = self.all_students
        no_moodle_info = [student for student in all_students if student.moodle_student_id is None]

        if len(no_moodle_info) == len(all_students):
            moodle_students = self._load_students_from_moodle(moodle)
            already_known = [student.moodle_student_id for student in all_students if
                             student.moodle_student_id is not None]

            print(f"There are already {len(already_known)} students matched.")
            moodle_students = [student for student in moodle_students if student[0] not in already_known]
            still_to_match = [(i, student) for i, student in enumerate(all_students) if
                              student.moodle_student_id is None]
            still_to_match = sorted(still_to_match, key=lambda tup: tup[1].muesli_mail)
            print(f'There are {len(moodle_students)} available students in moodle and {len(still_to_match)} to match.')

            match_students(all_students, still_to_match, moodle_students)

            print(f"No match for {len(still_to_match)} of {len(all_students)}")
            print()
            print_result_table(still_to_match, moodle_students)

            answer = input("Do you want to match the left column manually in case that there are matches left\n"
                           "which the automation didn't recognize? (y/n)\n"
                           ">: ")
            if answer == 'y':
                print("This feature is at the moment not supported... (storage.py:213)")

            print("Saving results...", end='')
            groups = defaultdict(list)

            for student in all_students:
                groups[student.tutorial_id].append(student)
            self.students = groups
            for tutorial_id in self.students:
                self.physical_storage.save_students(tutorial_id, self.students)
            print("[OK]")
        elif len(no_moodle_info) > 0:
            print(f"There are {len(no_moodle_info)} students, which are either not in Moodle or were not recognized"
                  f" in the first run.")
        else:
            print("All students are already with Moodle.")

    def _load_students_from_moodle(self, moodle: MoodleSession):
        print("Not all students are matched with their Moodle version.")
        print("Gathering information from Moodle...", end='')
        moodle_students = moodle.get_students(self.moodle_data.course_id, self.moodle_data.student_role)
        print("[Ok]")

        return moodle_students

    def _set_tutorial_ids(self, value, mode):
        if mode == 'my':
            self.my_tutorial_ids = value
        elif mode == 'other':
            self.other_tutorial_ids = value
        else:
            raise KeyError(f"Unknown id set '{mode}'!")

    def _get_tutorial_ids(self, mode):
        result = None
        if mode == 'my':
            result = self.my_tutorial_ids
        elif mode == 'other':
            result = self.other_tutorial_ids
        else:
            raise KeyError(f"Unknown id set '{mode}'!")

        return result

    @property
    def storage_config(self):
        return self.config.storage

    @property
    def muesli_account(self):
        return self.account_data.muesli

    @property
    def muesli_data(self):
        return self.config.muesli

    @property
    def moodle_account(self):
        return self.account_data.moodle

    @property
    def moodle_data(self):
        return self.config.moodle

    @property
    def all_students(self):
        return [student for k, students in self.students.items() for student in students]

    @property
    def my_students(self):
        return [student for student in self.all_students
                if student.tutorial_id in self.my_tutorial_ids
                or student.muesli_student_id in self.imported_students]

    @property
    def other_students(self):
        return [student for student in self.all_students
                if student.tutorial_id in self.other_tutorial_ids
                or student.muesli_student_id in self.exported_students]

    def list_students(self, tutorial_id):
        if tutorial_id in self.my_tutorial_ids:
            return [student for student in self.all_students
                    if student.tutorial_id == tutorial_id
                    or student.muesli_student_id in self.imported_students]
        else:
            return [student for student in self.all_students
                    if student.tutorial_id == tutorial_id
                    or student.muesli_student_id in self.exported_students]

    @property
    def my_tutorials(self):
        return [self.tutorials[tid] for tid in self.my_tutorial_ids]

    @property
    def other_tutorials(self):
        return [self.tutorials[tid] for tid in self.other_tutorial_ids]

    def export_student(self, student):
        self.exported_students.append(student.muesli_student_id)
        self.physical_storage.save_exchanged_students(self.exported_students, 'exported')

    def import_student(self, student):
        self.imported_students.append(student.muesli_student_id)
        self.physical_storage.save_exchanged_students(self.imported_students, 'imported')

    def get_tutorial_by_id(self, tutorial_id):
        if tutorial_id not in self.tutorials:
            raise KeyError(f"There is no tutorial with the id {tutorial_id}")
        return self.tutorials[tutorial_id]

    def get_all_students_of_tutorial(self, tutorial_id: int) -> list:
        return list(self.students[tutorial_id])

    def get_all_tutors(self) -> set:
        return {tutorial.tutor for tutorial in self.tutorials.values()}

    def get_students_by_name(self, name, mode='all'):
        if mode == 'all':
            all_students = self.all_students
        elif mode == 'my':
            all_students = self.my_students
        elif mode == 'other':
            all_students = self.other_students
        else:
            raise ValueError(f"Unknown mode '{mode}' in get_students_by_name (storage.py)")

        result = match_student(name, all_students)

        return list(result)

    def get_all_tutorials_of_tutor(self, tutor):
        return [tutorial for tutorial in self.tutorials.values() if tutorial.tutor == tutor]

    def download_submissions_of_my_students(self, moodle: MoodleSession, exercise_number, printer):
        printer.inform('Connecting to Moodle and collecting data.')
        printer.inform('This may take a few seconds.')
        submissions = moodle.find_submissions(
            self.moodle_data.course_id,
            self.moodle_data.exercise_prefix,
            exercise_number,
            printer
        )
        printer.inform(f"Found a total of {len(submissions)} for '{self.moodle_data.exercise_prefix}{exercise_number}'")
        my_students = self.my_students
        my_students = {student.moodle_student_id: student for student in my_students}

        submissions = [submission for submission in submissions if submission.moodle_student_id in my_students]
        printer.inform(f"Found {len(submissions)} submissions for me")

        folder = os.path.join(
            self.storage_config.root,
            self.storage_config.submission_root,
            f'{self.storage_config.exercise_template}{exercise_number}',
            self.storage_config.raw_folder
        )
        ensure_folder_exists(folder)
        for submission in submissions:
            with open(os.path.join(folder, submission.file_name), 'wb') as fp:
                try:
                    printer.inform(f"Downloading submission of {my_students[submission.moodle_student_id]} ... ",
                                   end='')
                    moodle.download(submission.url, fp)
                    printer.confirm('[Ok]')
                except Exception as e:
                    printer.error('[Err]')
                    printer.error(str(e))

        with open(os.path.join(folder, "meta.json"), 'w') as fp:
            try:
                printer.inform(f'Write meta data ... ', end='')
                j_dump([s.__dict__ for s in submissions], fp, indent=4)
                printer.confirm('[Ok]')
            except Exception as e:
                printer.error('[Err]')
                printer.error(str(e))

    def get_exercise_folder(self, exercise_number):
        return os.path.join(
            self.storage_config.root,
            self.storage_config.submission_root,
            f'{self.storage_config.exercise_template}{exercise_number}'
        )

    def get_raw_folder(self, exercise_number):
        return os.path.join(
            self.get_exercise_folder(exercise_number),
            self.storage_config.raw_folder
        )

    def get_preprocessed_folder(self, exercise_number):
        return os.path.join(
            self.get_exercise_folder(exercise_number),
            self.storage_config.preprocessed_folder
        )

    def get_working_folder(self, exercise_number):
        return os.path.join(
            self.get_exercise_folder(exercise_number),
            self.storage_config.working_folder
        )

    def update_exercise_meta(self, muesli, exercise_number):
        tutorial_id = self.my_tutorial_ids[0]
        exercise_id = muesli.get_exercise_id(tutorial_id, self.muesli_data.exercise_prefix, exercise_number)
        max_credits = muesli.get_max_credits_of(tutorial_id, exercise_id)
        max_credits = [[f'{self.muesli_data.feedback.task_prefix}{i + 1}', v] for i, v in enumerate(max_credits)]

        data = {
            "title": f'{self.muesli_data.feedback.exercise_title}{exercise_number}',
            "exercise_id": exercise_id,
            "max_credits": max_credits,
        }

        path = self._get_exercise_meta_path(exercise_number)
        with open(path, 'w', encoding='utf-8') as fp:
            j_dump(data, fp)

    def _get_exercise_meta_path(self, exercise_number):
        return os.path.join(self.get_exercise_folder(exercise_number), "exercise_meta.json")

    def has_exercise_meta(self, exercise_number):
        path = self._get_exercise_meta_path(exercise_number)
        return os.path.exists(path)

    def generate_feedback_template(self, exercise_number, target_path, printer):
        path = self._get_exercise_meta_path(exercise_number)
        if not self.has_exercise_meta(exercise_number):
            raise FileExistsError("The exercise meta data was not created")

        with open(path, 'r', encoding='utf-8') as fp:
            template_data = SimpleNamespace(**j_load(fp))

        with open(os.path.join(target_path, "submission_meta.json"), 'r', encoding='utf-8') as fp:
            submission_data = SimpleNamespace(**j_load(fp))

        lines = list()
        lines.append('┌' + '─' * 98 + '┐')
        lines.append(f'│{template_data.title:^98}│')
        lines.append('└' + '─' * 98 + '┘')
        lines.append(f'Abgegeben als: {submission_data.original_name}')
        lines.append('')

        if self.muesli_data.feedback.show_problems:
            if len(submission_data.problems) > 0:
                lines.append("Mit der Namensgebung der Datei gab es Probleme:")
                for problem in submission_data.problems:
                    lines.append("  ■ " + problem)
                lines.append("")
            else:
                lines.append("Die Benennung der war korrekt.")
                lines.append("")

        for task_name, max_credits in template_data.max_credits:
            max_credits = f'[Max: {max_credits}]'

            lines.append(f'{task_name:<100}'[:-len(max_credits)] + max_credits)
            lines.append('─' * 100)
            lines.append(self.muesli_data.feedback.default_answer)
            lines.append("")
            lines.append("")

        feedback_path = os.path.join(target_path, f'{self.muesli_data.feedback.file_name}.txt')

        if os.path.exists(feedback_path):
            printer.warning(f"There is already a generated feedback file at {target_path}."
                            f" Please remove it manually, if you want to recreate it.")

        else:
            with open(feedback_path, 'w', encoding='utf-8') as fp:
                for line in lines:
                    print(line, file=fp)


def match_student(input_name, list_of_students):
    def strip_accents(text):
        text = unicodedata.normalize('NFD', text) \
            .encode('ascii', 'ignore') \
            .decode("utf-8")

        return str(text)

    def preprocess_name(name):
        if name is None:
            return list()
        else:
            processed_name = name.lower()
            processed_name = processed_name.replace('ä', 'ae')
            processed_name = processed_name.replace('ö', 'oe')
            processed_name = processed_name.replace('ü', 'ue')
            processed_name = processed_name.replace('ß', 'ss')
            processed_name = strip_accents(processed_name)
            processed_name = processed_name.split()
            return processed_name

    for student in list_of_students:
        if preprocess_name(input_name) == preprocess_name(student.muesli_name):
            return [student]

    result = list()
    for student in list_of_students:
        result.append((preprocess_name(student.muesli_name), preprocess_name(student.moodle_name), student))

    for name_part in preprocess_name(input_name):
        tmp = list(result)
        for muesli_name, moodle_name, student in tmp:
            muesli_index, moodle_index = None, None
            for idx, muesli_name_part in enumerate(muesli_name):
                if name_part in muesli_name_part:
                    muesli_index = idx
                    break

            for idx, moodle_name_part in enumerate(moodle_name):
                if name_part in moodle_name_part:
                    moodle_index = idx
                    break

            if muesli_index is not None:
                del muesli_name[muesli_index]

            if moodle_index is not None:
                del moodle_name[moodle_index]

            if muesli_index is None and moodle_index is None:
                result.remove((muesli_name, moodle_name, student))

    return [student for _, _, student in result]