import os
import os.path
from collections import defaultdict
from json import load as j_load, dump as j_dump
from os.path import join as p_join
from time import sleep

from data.data import Student
from data.student_matching import match_students, print_result_table
from moodle.api import MoodleSession
from muesli.api import Tutorial, MuesliSession
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
            j_dump(my_name, fp)

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
            j_dump(ids, fp)

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
            j_dump({k: v.to_json() for k, v in tutorials.items()}, fp)

    def load_tutorial_data(self):
        path = p_join(self._meta_path, f'03_tutorials.json')
        result = dict(), "Missing"
        if os.path.exists(path):
            with open(path, 'r') as fp:
                result = {k: Tutorial.from_json(v) for k, v in j_load(fp).items()}, "Loaded"

        return result

    def save_students(self, tutorial_id, students):
        directory = ensure_folder_exists(p_join(self._meta_path, "students"))
        path = p_join(directory, f'students_{tutorial_id}.json')
        with open(path, 'w') as fp:
            out_data = [student.to_json_dict() for student in students[tutorial_id]]
            j_dump(out_data, fp)

    def load_students(self, tutorial_id):
        directory = ensure_folder_exists(p_join(self._meta_path, "students"))
        path = p_join(directory, f'students_{tutorial_id}.json')
        result = list(), "Missing"
        if os.path.exists(path):
            with open(path, 'r') as fp:
                result = [Student.from_json(student) for student in j_load(fp)], "Loaded"

        return result


class InteractiveDataStorage:
    __instance = None

    def __new__(cls):
        if InteractiveDataStorage.__instance is None:
            InteractiveDataStorage.__instance = object.__new__(cls)
        InteractiveDataStorage.__instance.my_name = None
        InteractiveDataStorage.__instance.my_tutorial_ids = list()
        InteractiveDataStorage.__instance.other_tutorial_ids = list()
        InteractiveDataStorage.__instance.tutorials = dict()
        InteractiveDataStorage.__instance.students = dict()
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

    def _init_my_name(self, muesli: MuesliSession):
        print(f"Load my name ...", end='')
        my_name, state = self.__instance.physical_storage.load_my_name()
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

            self.__instance.my_name = names[index]
            self.__instance.physical_storage.save_my_name(self.__instance.my_name)

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

    def _init_tutorials(self, muesli: MuesliSession):
        print(f"Load tutorial data...", end='')
        tutorials, state = self.__instance.physical_storage.load_tutorial_data()
        self.__instance.tutorials = tutorials
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
        all_students = [student for k, students in self.students.items() for student in students]
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
            self.__instance.my_tutorial_ids = value
        elif mode == 'other':
            self.__instance.other_tutorial_ids = value
        else:
            raise KeyError(f"Unknown id set '{mode}'!")

    def _get_tutorial_ids(self, mode):
        result = None
        if mode == 'my':
            result = self.__instance.my_tutorial_ids
        elif mode == 'other':
            result = self.__instance.other_tutorial_ids
        else:
            raise KeyError(f"Unknown id set '{mode}'!")

        return result

    @property
    def storage_config(self):
        return self.__instance.config.storage

    @property
    def muesli_account(self):
        return self.__instance.account_data.muesli

    @property
    def muesli_data(self):
        return self.__instance.config.muesli

    @property
    def moodle_account(self):
        return self.__instance.account_data.moodle

    @property
    def moodle_data(self):
        return self.__instance.config.moodle

    def update_tutorials(self, muesli: MuesliSession, mode="my"):
        if mode == "my":
            tutorials = muesli.get_my_tutorials(self.muesli_data.lecture_id, self.__instance.my_name)
            ids = self.__instance.my_tutorial_ids
        elif mode == "other":
            tutorials = muesli.get_all_tutorials_of_lecture(self.muesli_data.lecture_id,
                                                            except_ids=self.__instance.my_tutorial_ids)
            ids = self.__instance.other_tutorial_ids
        else:
            raise ValueError(f"Unknown mode '{mode}'!")

        ids.clear()
        for tutorial in tutorials:
            tid = tutorial.tutorial_id
            self.__instance.tutorials[tid] = tutorial
            ids.append(tid)

        self.__instance.physical_storage.save_tutorial_ids(ids, mode)
        self.__instance.physical_storage.save_tutorial_data(self.__instance.tutorials)

    def update_students_of_tutorial(self, muesli: MuesliSession, tutorial_id: int):
        students = muesli.get_all_students_of_tutorial(tutorial_id)
        self.__instance.students[tutorial_id] = students
        self.__instance.physical_storage.save_students(tutorial_id, self.__instance.students)

    @property
    def my_tutorials(self):
        return [self.__instance.tutorials[tid] for tid in self.my_tutorial_ids]

    @property
    def other_tutorials(self):
        return [self.__instance.tutorials[tid] for tid in self.other_tutorial_ids]

    def get_all_students_of_tutorial(self, tutorial_id: int) -> list:
        return list(self.__instance.students[tutorial_id])

    def get_all_tutors(self) -> set:
        return {tutorial.tutor for tutorial in self.tutorials.values()}
