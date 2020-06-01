import os
import re
from json import dump as j_dump

from data.storage import ensure_folder_exists
from util.console import string_table, align_vertical


class FeedbackPolisher:
    def __init__(self, storage, path, printer):
        self.printer = printer
        self._storage = storage
        self._task_prefix = storage.muesli_data.feedback.task_prefix
        self._file_name = f"{self._storage.muesli_data.feedback.file_name}.txt"
        self._path = os.path.join(path, self._file_name)
        self._students = self._find_students()
        self._segments = self._read_segments()

        self._analyze_credit_annotations()
        self._generate_salutation()

        table, self._credits_per_task = self._generate_table()
        self._feedback = self._polish_feedback(table)

    def _read_segments(self):
        segments = dict()
        with open(self._path, 'r', encoding='utf-8') as fp:
            task_pattern = re.compile(self._task_prefix + r'(?P<task_number>\d)\s+\[Max: (?P<max_credit>\d+\.\d+)\]')
            buffer = list()
            group_type = "__intro__"
            for line in fp:
                line = line[:-1]
                matcher = task_pattern.match(line)
                if matcher:
                    task_number = int(matcher.group("task_number"))
                    max_credits = float(matcher.group("max_credit"))
                    if group_type == "__intro__":
                        segments[group_type] = {"lines": list(buffer)}
                    else:
                        segments[group_type]["lines"] = list(buffer)
                    group_type = task_number
                    segments[group_type] = {"task_number": task_number, "max_credits": max_credits}
                    buffer = list()
                buffer.append(line)
            segments[group_type]["lines"] = list(buffer)

        return segments

    def _analyze_credit_annotations(self):
        credit_pattern = re.compile(r'\[@(?P<credit>([-+])?\d+(\.\d+)?)\]')

        for group_type, group in self._segments.items():
            if group_type != "__intro__":
                max_credits = group["max_credits"]
                achieved_credits = max_credits
                for line in group["lines"]:
                    for entry in re.findall(credit_pattern, line):
                        credit = float(entry[0])
                        achieved_credits += credit
                group["achieved_credits"] = (achieved_credits if achieved_credits >= 0.0 else 0.0)

                task_name = f'{self._task_prefix} {group["task_number"]}'
                stats = f'[{achieved_credits} / {max_credits}]'
                line = f'{task_name:<100}'[:-len(stats)] + stats
                group["lines"][0] = line

    def _generate_table(self):
        header, data = list(), list()
        max_total, achieved_total = 0, 0
        for group_type, group in self._segments.items():
            if group_type != "__intro__":
                max_credits = group["max_credits"]
                achieved_credits = group["achieved_credits"]

                header.append(f"{self._task_prefix[0]} {group['task_number']} ({max_credits})")
                data.append((achieved_credits,))
                max_total += max_credits
                achieved_total += achieved_credits

        credits_per_task = [credit for column in data for credit in column]
        header.append(f'∑ ({max_total})')
        data.append((achieved_total,))
        table = string_table(header, data, align_row='^')

        return table, credits_per_task

    def _generate_salutation(self):
        self._salutation = list()
        self._salutation.append("Dieses Feedback ist für:")
        for student in self._students:
            self._salutation.append(f"• {student.muesli_name} ({student.muesli_mail})")
        max_length = max([len(_) for _ in self._salutation])
        for i in range(len(self._salutation)):
            self._salutation[i] = (self._salutation[i] + (' ' * max_length))[:max_length]

    def _find_students(self):
        camel_case_pattern = re.compile(r'[A-Z](?:[a-zöäüß]+|[A-Z]*(?=[A-Z]|$))')
        merged_name = os.path.basename(os.path.dirname(self._path))
        student_names_raw = merged_name.split('_')[:-1]
        students = list()

        for student_name in student_names_raw:
            parts = camel_case_pattern.findall(student_name[0].upper() + student_name[1:])
            if len(parts) > 0:
                student_name = ("-".join(parts))

            student_name = student_name.split("-")
            student_name = " ".join(student_name)
            possible_students = self._storage.get_students_by_name(student_name, mode='my')
            if len(possible_students) == 0:
                possible_students = self._storage.get_students_by_name(student_name, mode='all')

            if len(possible_students) == 1:
                students.append(possible_students[0])
            elif len(possible_students) == 0:
                self.printer.warning(f"No student found with name '{student_name}'. [IGNORE]")
            else:
                location = '(feedback.py: FeedbackPolisher._find_students)'
                message = f"Did not expect {len(possible_students)} possible students for '{student_name}'. {location}"
                raise ValueError(message)

        return students

    def _polish_feedback(self, table):
        table = ["\n"] + table + ["\n"]

        feedback = self._segments["__intro__"]["lines"]
        feedback = align_vertical(feedback, self._salutation, alignment='^')
        feedback = align_vertical(feedback, table, alignment='^')
        for group_type, group in self._segments.items():
            if group_type != "__intro__":
                feedback = align_vertical(feedback, group["lines"])

        footer = list()
        footer.append("\n")
        footer.append('═' * 100)
        footer.append(f"Dieses Feedback wurde von {self._storage.my_name_alias} ({self._storage.my_name}) erstellt.")
        footer.append(f"Fragen zur Korrektur könnt ihr gerne per Mail ({self._storage.muesli_account.email})")
        footer.append(f"oder per Privatnachricht in Discord stellen.")

        feedback = align_vertical(feedback, footer)

        return feedback

    def save_meta_to_folder(self, directory):
        ensure_folder_exists(directory)
        meta_data = dict()
        meta_data["credits_per_task"] = self._credits_per_task
        meta_data["names"] = [student.muesli_name for student in self._students]
        meta_data["muesli_ids"] = [student.muesli_student_id for student in self._students]
        meta_data["muesli_mails"] = [student.muesli_mail for student in self._students]

        with open(os.path.join(directory, "meta.json"), 'w', encoding="utf-8") as fp:
            j_dump(meta_data, fp, indent=4)

        feedback_path = os.path.join(directory, self._file_name)
        with open(feedback_path, 'w', encoding="utf-8") as fp:
            for line in self._feedback:
                print(line, file=fp)
