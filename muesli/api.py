import re

from bs4 import BeautifulSoup
from requests import Session

from data.data import Student, Tutorial


class MuesliSession:
    def __init__(self, account):
        self._session = None
        self._account = account
        self._logout_url = None
        self._test_url = 'https://muesli.mathi.uni-heidelberg.de/start'
        self._present_urls = dict()

    @property
    def name(self):
        return f"Muesli [{self.get_online_state()}]"

    @property
    def online(self):
        return self.get_online_state() == 'online'

    def get(self, url, parse=True):
        result = self._session.get(url)
        if result.status_code == 200 and parse:
            result = BeautifulSoup(result.content, "html.parser")
        else:
            if self.online:
                raise ConnectionError(f"Http GET failed with {result.status_code}.")
            else:
                raise ConnectionRefusedError(f"MÜSLI is not online, please login first.")

        return result

    def get_online_state(self):
        result = 'offline'
        if self._session is not None:
            response = self._session.get(self._test_url)

            if 302 in [r.status_code for r in response.history] or response.status_code == 302:
                result = 'login required'
            elif response.status_code == 200:
                result = 'online'
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
        error_element = soup.find('p', attrs={'class': 'error'})
        if error_element is not None:
            raise ConnectionRefusedError('Wrong username or password.')

        self._logout_url = 'https://muesli.mathi.uni-heidelberg.de/user/logout'

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logout()

    def logout(self):
        try:
            self.get(self._logout_url, parse=False)
        except ConnectionRefusedError:
            # already logged out
            pass
        self._logout_url = None
        self._session.close()
        self._session = None

    def get_my_tutorials(self, lecture_id, my_name):
        soup = self.get(f'https://muesli.mathi.uni-heidelberg.de/lecture/view/{lecture_id}')
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
        soup = self.get(f'https://muesli.mathi.uni-heidelberg.de/lecture/view/{lecture_id}')
        table = soup.find('table')
        result = None

        for row in table.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) > 0 and tutorial_id == MuesliSession._extract_id(cols[5]):
                result = cols[3].text.strip()
                break

        return result

    def _add_details_to_tutorial(self, tutorial):
        soup = self.get(f'https://muesli.mathi.uni-heidelberg.de/tutorial/view/{tutorial.tutorial_id}')
        tutorial.tutor_mail = soup.find('p').find('a')['href'][len("mailto:"):]

    def get_all_students_of_tutorial(self, tutorial_id):
        soup = self.get(f'https://muesli.mathi.uni-heidelberg.de/tutorial/view/{tutorial_id}')
        result = list()

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

        return result

    def get_all_tutorials_of_lecture(self, lecture_id, except_ids=tuple()):
        soup = self.get(f'https://muesli.mathi.uni-heidelberg.de/lecture/view/{lecture_id}')
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
        soup = self.get(f'https://muesli.mathi.uni-heidelberg.de/lecture/view/{lecture_id}')
        table = soup.find('table')

        return {row.find_all('td')[3].text.strip() for row in table.find_all('tr') if len(row.find_all('td')) > 0}

    def get_exercise_id(self, tutorial_id, exercise_prefix, exercise_number):
        soup = self.get(f'https://muesli.mathi.uni-heidelberg.de/tutorial/view/{tutorial_id}')
        return soup.find('a', text=f"{exercise_prefix}{exercise_number}")['href'].split("/")[-2]

    def get_max_credits_of(self, tutorial_id, exercise_id):
        soup = self.get(f"https://muesli.mathi.uni-heidelberg.de/exam/statistics/{exercise_id}/{tutorial_id}")
        columns = soup.find('table').find_all('tr')[-1].find_all('td')[1:-1]
        max_credits = [float(column.text) for column in columns]
        return max_credits

    def get_scores_of(self, tutorial_id, exam_id):
        raise NotImplementedError("Not implemented yet!")

    def set_scores_of(self, tutorial_id, exam_id, scores):
        raise NotImplementedError("Not implemented yet!")

    def update_presented(self, student, present_name):
        tutorial_id = student.tutorial_id
        present_url = self._get_presented_url(present_name, tutorial_id)

        soup = self.get(present_url)
        table = soup.find("table", attrs={'class': 'colored'})
        table_row = table.find('tr', attrs={'id': f'row-{student.muesli_student_id}'})
        data = dict()
        rows = table.find_all('tr')
        for row in rows[1:-5]:
            columns = row.find_all('td')
            if len(columns) > 0:
                input_score = columns[1].find('input')
                name = input_score['name']
                try:
                    value = float(input_score['value'])
                except KeyError:
                    value = ''
                data[name] = value
        input_points = table_row.find_all('td')[1].find('input', attrs={'class': 'points', 'type': 'text'})

        data['submit'] = 1
        data[input_points['name']] = 1
        response = self._session.post(present_url, data=data)

        return response.status_code == 200

    def _get_presented_url(self, present_name, tutorial_id):
        if tutorial_id in self._present_urls:
            present_url = self._present_urls[tutorial_id]
        else:
            soup = self.get(f'https://muesli.mathi.uni-heidelberg.de/tutorial/view/{tutorial_id}')
            present_id = soup.find('a', text=f"{present_name}")['href'].split("/")[-2]
            present_url = f"https://muesli.mathi.uni-heidelberg.de/exam/enter_points/{present_id}/{tutorial_id}"
            self._present_urls[tutorial_id] = present_url

        return present_url

    def get_presented_table(self, present_name, tutorial_id):
        present_url = self._get_presented_url(present_name, tutorial_id)
        soup = self.get(present_url)
        table = soup.find("table", attrs={'class': 'colored'})
        data = dict()
        rows = table.find_all('tr')
        for row in rows[1:-5]:
            muesli_student_id = int(row['id'].split('-')[1])
            columns = row.find_all('td')
            input_score = columns[1].find('input')

            try:
                value = float(input_score['value'])
                if value > 0.0:
                    value = True
                else:
                    value = False
            except KeyError:
                value = False
            data[muesli_student_id] = value

        return data

    def upload_credits(self, tutorial_id, exercise_id, credit_data):
        credits_url = f"https://muesli.mathi.uni-heidelberg.de/exam/enter_points/{exercise_id}/{tutorial_id}"

        soup = self.get(credits_url)
        table = soup.find("table", attrs={'class': 'colored'})
        rows = table.find_all('tr', id=re.compile(r'row-\d+'))
        rows = {row['id']: row for row in rows}
        data = dict()
        number_of_changes = 0

        for row_id, row in rows.items():
            for idx, column in enumerate(row.find_all('input')[:-1]):
                try:
                    data[column['name']] = float(column['value'])
                except KeyError:
                    credit = credit_data.get(int(row_id[4:]))
                    if credit is not None:
                        credit = credit[idx]
                    data[column['name']] = credit
                    if data[column['name']] is not None:
                        number_of_changes += 1

        data['submit'] = 1
        response = self._session.post(credits_url, data=data)
        return response.status_code == 200, number_of_changes
