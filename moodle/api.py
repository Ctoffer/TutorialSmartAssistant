import re
from types import SimpleNamespace

from bs4 import BeautifulSoup
from requests import Session


class MoodleSession:
    def __init__(self, account):
        self._session = None
        self._account = account
        self._logout_url = None
        self._test_url = 'https://moodle.uni-heidelberg.de/user/profile.php'

    @property
    def name(self):
        return f"Moodle [{self.get_online_state()}]"

    @property
    def online(self):
        return self.get_online_state() == 'online'

    def get_online_state(self):
        result = 'offline'
        if self._session is not None:
            response = self._session.get(self._test_url)
            if response.status_code == 200:
                result = 'online'
            elif response.status_code == 303:
                result = 'login required'
            else:
                result = 'offline'
        return result

    def __enter__(self):
        self.login()
        return self

    def login(self):
        def contains_login_token(elem):
            return elem["type"] == "hidden" and elem["name"] == "logintoken"

        self._session = Session()
        login_url = "https://moodle.uni-heidelberg.de/login/index.php"
        website = self._session.get(url=login_url)
        soup = BeautifulSoup(website.content, "html.parser")
        login_token = [inp for inp in soup.find_all('input') if contains_login_token(inp)][0]["value"]

        r = self._session.post(login_url, data={
            "anchor": "",
            "username": self._account.name,
            "password": self._account.password,
            "logintoken": login_token
        })
        soup = BeautifulSoup(r.content, "html.parser")
        error_element = soup.find('p', attrs={'class': 'a', 'id': 'loginerrormessage'})
        if error_element is not None:
            raise ConnectionRefusedError('Wrong username or password.')
        self._logout_url = soup.find_all("a", attrs={"role": "menuitem", "data-title": "logout,moodle"})[0]["href"]

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logout()

    def logout(self):
        self._session.post(self._logout_url)
        self._logout_url = None
        self._session.close()
        self._session = None

    def get_course_page(self, course_id):
        course_url = f"https://moodle.uni-heidelberg.de/course/view.php?id={course_id}"
        response = self._session.get(course_url)
        return BeautifulSoup(response.content, "html.parser")

    def get_students(self, course_id, student_role):
        url = f'https://moodle.uni-heidelberg.de/user/index.php?id={course_id}&perpage=5000'
        response = self._session.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', attrs={'class': 'flexible generaltable generalbox'}).find('tbody')
        students = list()

        for row in table.find_all('tr'):
            columns = row.find_all('td')
            anchor = columns[1].find('a')
            if anchor is not None and columns[3].text == student_role:
                name, profile_url = columns[1].text, anchor['href']
                matcher = re.search(r'.*id=(\d+)&.*', profile_url)
                moodle_id = matcher.group(1)
                mail = columns[2].text
                students.append((int(moodle_id), name, mail))

        students = sorted(students, key=lambda t: t[2])
        return students

    def find_submissions(self, course_id, exercise_prefix, exercise_number, printer):
        def is_matching_id(x):
            return x and x.startswith('section-')

        def is_matching_label(x):
            return x and x.startswith(f'{exercise_prefix}{exercise_number}')

        def is_matching_url(x):
            return x and x.startswith('https://moodle.uni-heidelberg.de/mod/assign/view.php?id=')

        soup = self.get_course_page(course_id)
        table = soup.find('ul', attrs={'class': 'topics'})
        section = table.find('li', attrs={"id": is_matching_id, "aria-label": is_matching_label})
        submission_link = section.find('a', attrs={'href':is_matching_url})['href'] + "&action=grading"

        soup = self._show_all_submissions(submission_link)
        rows = soup.find('table').find('tbody').find_all('tr')

        result = list()
        for row in rows:
            columns = row.find_all('td')
            moodle_student_id = int(columns[0].find('input', attrs={'type':'checkbox'})['value'])
            name = columns[2].find('a').text
            download_anchor = columns[8].find_all('a', attrs={'target':'_blank'})

            if len(download_anchor) > 0:
                if len(download_anchor) > 1:
                    printer.warning(f"'{name}' has uploaded more than one submission! Using latest...")
                    download_anchor = download_anchor[-1]
                else:
                    download_anchor = download_anchor[0]

                submission_name = download_anchor.text
                submission_url = download_anchor['href']
                data = {
                    "moodle_student_id":moodle_student_id,
                    "file_name": submission_name,
                    "url": submission_url
                }
                result.append(SimpleNamespace(**data))

        return result

    def _show_all_submissions(self, submission_link):
        soup = BeautifulSoup(self._session.post(submission_link).content, 'html.parser')
        context_id = soup.find('input', attrs={'name': 'contextid', 'type': 'hidden'})['value']
        page_id = soup.find('input', attrs={'name': 'id', 'type': 'hidden'})['value']
        user_id = soup.find('input', attrs={'name': 'userid', 'type': 'hidden'})['value']

        response = self._session.post(submission_link, data={
            'id': page_id,
            'perpage': -1,
            'action': 'saveoptions',
            'contextid': context_id,
            'userid': user_id,
            'sesskey': self._logout_url.split('sesskey=')[1],
            '_qf__mod_assign_grading_options_form': 1,
            'mform_isexpanded_id_general': 1,
            'filter': None,
            'downloadasfolders': 1,
        })
        import time
        time.sleep(3)
        return BeautifulSoup(response.content, "html.parser")

    def download(self, source, target):
        target.write(self._session.get(source).content)
