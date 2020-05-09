class Student:
    def __init__(self, tutorial_id, muesli_student_id, muesli_name, muesli_mail, subject):
        self._tutorial_id = tutorial_id
        self._muesli_student_id = muesli_student_id
        self._muesli_name = muesli_name
        self._muesli_mail = muesli_mail
        self._subject = subject

        self._moodle_student_id = None
        self._moodle_name = None
        self._moodle_mail = None

        self.alias = self._muesli_name.split()[0]

    @property
    def tutorial_id(self):
        return self._tutorial_id

    @property
    def muesli_student_id(self):
        return self._muesli_student_id

    @property
    def muesli_name(self):
        return self._muesli_name

    @property
    def muesli_mail(self):
        return self._muesli_mail

    @property
    def subject(self):
        return self._subject

    def set_moodle_identity(self, moodle_student_id, moodle_name, moodle_mail):
        self._moodle_student_id = moodle_student_id
        self._moodle_name = moodle_name
        self._moodle_mail = moodle_mail

    @property
    def moodle_student_id(self):
        return self._moodle_student_id

    @property
    def moodle_name(self):
        return self._moodle_name

    @property
    def moodle_mail(self):
        return self._moodle_mail

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f'{self._muesli_name} ({self._muesli_student_id})'

    def to_json_dict(self):
        return {"tutorial_id": self._tutorial_id,
                "muesli_student_id": self._muesli_student_id,
                "muesli_name": self._muesli_name,
                "muesli_mail": self._muesli_mail,
                "subject": self._subject,
                "moodle_student_id": self._moodle_student_id,
                "moodle_name": self._moodle_name,
                "moodle_mail": self._moodle_mail,
                "alias": self.alias}

    @staticmethod
    def from_json(dictionary):
        student = Student(dictionary["tutorial_id"],
                dictionary["muesli_student_id"],
                dictionary["muesli_name"],
                dictionary["muesli_mail"],
                dictionary["subject"])
        student.set_moodle_identity(dictionary["moodle_student_id"],
                                    dictionary["moodle_name"],
                                    dictionary["moodle_mail"])
        student.alias = dictionary["alias"]
        return student
