from bs4 import BeautifulSoup
from requests import Session

from data.data import Student


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


class MuesliSession:
    def __init__(self, account):
        self._session = None
        self._account = account
        self._logout_url = None

    def __enter__(self):
        self._session = Session()
        self._login()
        return self

    def _login(self):
        login_url = 'https://muesli.mathi.uni-heidelberg.de/user/login'
        self._session.post(login_url, data={
            'email': self._account.email,
            'password': self._account.password
        })
        self._logout_url = 'https://muesli.mathi.uni-heidelberg.de/user/logout'

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._logout()
        self._session.close()
        self._session = None

    def _logout(self):
        self._session.get(self._logout_url)
        self._logout_url = None

    def get_my_tutorials(self, lecture_id, my_name):
        response = self._session.get(f'https://muesli.mathi.uni-heidelberg.de/lecture/view/{lecture_id}')
        soup = BeautifulSoup(response.content, "html.parser")
        lecture_name = soup.find('h2').text
        table = soup.find('table')
        result = list()

        for row in table.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) > 0:
                tutorial_id = MuesliSession._extract_id(cols[5])
                time, location, tutor = cols[0], cols[1], cols[3].text.strip()
                if tutor == my_name:
                    time = time.text.strip()
                    location = location.text.strip()

                    tutorial = Tutorial(lecture_name=lecture_name,
                                        lecture_id=lecture_id,
                                        tutorial_id=tutorial_id,
                                        tutor=tutor,
                                        time=time,
                                        location=location)
                    self._add_details_to_tutorial(tutorial)
                    result.append(tutorial)

        return result

    @staticmethod
    def _extract_id(element):
        if element.name == 'a':
            anchor = element
            partial_url = anchor['href']
        elif element.name == 'form':
            partial_url = element['action']
        else:
            anchor = element.find('a')
            partial_url = anchor['href']
        some_id = partial_url.split('/')[-1]
        return int(some_id)

    def _get_name_of_tutor(self, lecture_id, tutorial_id):
        response = self._session.get(f'https://muesli.mathi.uni-heidelberg.de/lecture/view/{lecture_id}')
        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find('table')
        result = None

        for row in table.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) > 0 and tutorial_id == MuesliSession._extract_id(cols[5]):
                result = cols[3].text.strip()
                break

        return result

    def _add_details_to_tutorial(self, tutorial):
        response = self._session.get(f'https://muesli.mathi.uni-heidelberg.de/tutorial/view/{tutorial.tutorial_id}')

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            tutorial.tutor_mail = soup.find('p').find('a')['href'][len("mailto:"):]
        elif response.status_code == 403:
            # TODO do sth usefull here with a custom logger...
            pass

    def get_all_students_of_tutorial(self, tutorial_id):
        response = self._session.get(f'https://muesli.mathi.uni-heidelberg.de/tutorial/view/{tutorial_id}')
        result = list()

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            table = soup.find('table').find('tbody')
            for row in table.find_all('tr'):
                cols = row.find_all('td')
                mail = cols[0].find('a')['href'][len("mailto:"):]
                name = cols[0].text
                subject = cols[1].text
                muesli_student_id = MuesliSession._extract_id(cols[2].find('form'))
                student = Student(tutorial_id=tutorial_id,
                                  muesli_student_id=muesli_student_id,
                                  muesli_name=name,
                                  muesli_mail=mail,
                                  subject=subject)
                result.append(student)
        elif response.status_code == 403:
            # TODO do sth usefull here with a custom logger...
            pass

        return result

    def get_all_tutorials_of_lecture(self, lecture_id, except_ids=tuple()):
        response = self._session.get(f'https://muesli.mathi.uni-heidelberg.de/lecture/view/{lecture_id}')
        soup = BeautifulSoup(response.content, "html.parser")
        lecture_name = soup.find('h2').text
        table = soup.find('table')
        result = list()

        for row in table.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) > 0:
                tutorial_id = MuesliSession._extract_id(cols[5])
                time, location, tutor = cols[0], cols[1], cols[3]
                if tutorial_id not in except_ids:
                    time = time.text.strip()
                    location = location.text.strip()
                    tutor = tutor.text.strip()

                    tutorial = Tutorial(lecture_name=lecture_name,
                                        lecture_id=lecture_id,
                                        tutorial_id=tutorial_id,
                                        tutor=tutor,
                                        time=time,
                                        location=location)
                    self._add_details_to_tutorial(tutorial)
                    result.append(tutorial)

        return result

    def get_tutor_names(self, lecture_id):
        response = self._session.get(f'https://muesli.mathi.uni-heidelberg.de/lecture/view/{lecture_id}')
        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find('table')

        return {row.find_all('td')[3].text.strip() for row in table.find_all('tr') if len(row.find_all('td')) > 0}

    def get_exams_of(self, tutorial_id):
        raise NotImplementedError("Not implemented yet!")

    def get_scores_of(self, tutorial_id, exam_id):
        raise NotImplementedError("Not implemented yet!")

    def set_scores_of(self, tutorial_id, exam_id, scores):
        raise NotImplementedError("Not implemented yet!")
