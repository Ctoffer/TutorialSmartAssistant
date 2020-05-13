class Tutorial:
    def __init__(self, lecture_name, lecture_id, tutorial_id, tutor, time, location):
        self._lecture_name = lecture_name
        self._lecture_id = int(lecture_id)
        self._tutorial_id = int(tutorial_id)
        self._tutor = tutor
        self.tutor_mail = None
        self._time = time
        self._location = location

    @property
    def lecture_name(self):
        return self._lecture_name

    @property
    def lecture_id(self):
        return self._lecture_id

    @property
    def tutorial_id(self):
        return self._tutorial_id

    @property
    def tutor(self):
        return self._tutor

    @property
    def time(self):
        return self._time

    @property
    def location(self):
        return self._location

    def __str__(self):
        parts = self.tutor.split()
        name = f"{parts[0][0]}. {parts[-1]}"
        return f'Tutorial({self.lecture_id}, {self.tutorial_id}, {self.time} - {self.location}, {name})'

    def __repr__(self):
        return str(self)

    def to_json(self):
        return {
            "lecture_name": self._lecture_name,
            "lecture_id": self._lecture_id,
            "tutorial_id": self._tutorial_id,
            "tutor": self._tutor,
            "tutor_mail": self.tutor_mail,
            "time": self._time,
            "location": self._location
        }

    @staticmethod
    def from_json(dictionary):
        tutorial = Tutorial(
            dictionary['lecture_name'],
            dictionary['lecture_id'],
            dictionary['tutorial_id'],
            dictionary['tutor'],
            dictionary['time'],
            dictionary['location']
        )
        tutorial.tutor_mail = dictionary['tutor_mail']
        return tutorial


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
    def muesli_data(self):
        return {
            "Tutorial-Id": self.tutorial_id,
            "Id": self.muesli_student_id,
            "Name": self.muesli_name,
            "E-Mail": self.muesli_mail,
            "Subject": self.subject
        }

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
    def moodle_data(self):
        return {
            "Id": self.moodle_student_id,
            "Name": self.moodle_name,
            "E-Mail": self.moodle_mail,
        }

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
