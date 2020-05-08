from bs4 import BeautifulSoup
from requests import Session


class Tutorial:
    def __init__(self, lecture_name, lecture_id, tutorial_id, tutor, time, location):
        self._lecture_name = lecture_name
        self._lecture_id = lecture_id
        self._tutorial_id = tutorial_id
        self._tutor = tutor
        self.tutor_mail = None
        self._time = time
        self._location = location
        self.participants = list()

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

    def get_my_tutorials(self):
        def normalize_columns(columns):
            for i in range(len(columns)):
                anchor = columns[i].find('a')
                if anchor is not None:
                    columns[i] = columns[i].text.strip(), anchor['href'].split('/')[-1]
                else:
                    columns[i] = columns[i].text.strip()

        response = self._session.get('https://muesli.mathi.uni-heidelberg.de/start')
        soup = BeautifulSoup(response.content, "html.parser")
        table_body = soup.find('table')
        tutorials = list()

        for row in table_body.find_all('tr'):
            cols = row.find_all('td')

            if len(cols) > 0:
                normalize_columns(cols)
                semester, (name, lecture_id), time, location, (_, tutorial_id) = cols

                tutor = self._get_name_of_tutor(lecture_id, tutorial_id)
                tutorial = Tutorial(lecture_name=name,
                                    lecture_id=lecture_id,
                                    tutorial_id=tutorial_id,
                                    tutor=tutor,
                                    time=time,
                                    location=location)
                tutorials.append(tutorial)

        return tutorials

    def _get_name_of_tutor(self, lecture_id, tutorial_id):
        response = self._session.get(f'https://muesli.mathi.uni-heidelberg.de/lecture/view/{lecture_id}')
        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find('table')
        result = None

        for row in table.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) > 0 and tutorial_id in cols[5].find('a')['href']:
                result = cols[3].text.strip()
                break

        return result

    def get_all_tutorials_of_lecture(self, lecture_id, except_ids=tuple()):
        pass