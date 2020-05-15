from bs4 import BeautifulSoup
from requests import Session

from data.data import Student, Tutorial


class MuesliSession:
    def __init__(self, account):
        self._session = None
        self._account = account
        self._logout_url = None
        self._test_url = 'https://muesli.mathi.uni-heidelberg.de/start'

    @property
    def name(self):
        return f"Muesli [{self.get_online_state()}]"

    @property
    def online(self):
        return self.get_online_state() == 'online'

    def get_online_state(self):
        result = 'offline'
        if self._session is not None:
            response = self._session.get(self._test_url)
            if response.status_code == 200:
                result = 'online'
            elif response.status_code == 302:
                result = 'login required'
            else:
                result = 'offline'
        return result

    def __enter__(self):
        self.login()
        return self

    def login(self):
        self._session = Session()
        login_url = 'https://muesli.mathi.uni-heidelberg.de/user/login'
        response = self._session.post(login_url, data={
            'email': self._account.email,
            'password': self._account.password
        })
        soup = BeautifulSoup(response.content, 'html.parser')
        error_element = soup.find('p', attrs={'class':'error'})
        if error_element is not None:
            raise ConnectionRefusedError('Wrong username or password.')

        self._logout_url = 'https://muesli.mathi.uni-heidelberg.de/user/logout'

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logout()

    def logout(self):
        self._session.get(self._logout_url)
        self._logout_url = None
        self._session.close()
        self._session = None

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

    def get_exercise_id(self, tutorial_id, exercise_prefix, exercise_number):
        response = self._session.get(f'https://muesli.mathi.uni-heidelberg.de/tutorial/view/{tutorial_id}')
        soup = BeautifulSoup(response.content, "html.parser")
        return soup.find('a', text=f"{exercise_prefix}{exercise_number}")['href'].split("/")[-2]

    def get_max_credits_of(self, tutorial_id, exercise_id):
        response = self._session.get(f"https://muesli.mathi.uni-heidelberg.de/exam/statistics/{exercise_id}/{tutorial_id}")
        soup = BeautifulSoup(response.content, "html.parser")
        columns = soup.find('table').find_all('tr')[-1].find_all('td')[1:-1]
        max_credits = [float(column.text) for column in columns]
        return max_credits

    def get_scores_of(self, tutorial_id, exam_id):
        raise NotImplementedError("Not implemented yet!")

    def set_scores_of(self, tutorial_id, exam_id, scores):
        raise NotImplementedError("Not implemented yet!")
