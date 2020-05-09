import re

from bs4 import BeautifulSoup
from requests import Session


class MoodleSession:
    def __init__(self, account):
        self._session = None
        self._account = account
        self._logout_url = None

    def __enter__(self):
        self._session = Session()
        self._login()
        return self

    def _login(self):
        def contains_login_token(elem):
            return elem["type"] == "hidden" and elem["name"] == "logintoken"

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
        self._logout_url = soup.find_all("a", attrs={"role": "menuitem", "data-title": "logout,moodle"})[0]["href"]

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._logout()
        self._session.close()
        self._session = None

    def _logout(self):
        self._session.post(self._logout_url)
        self._logout_url = None

    def get_course_page(self, course_id):
        course_url = f"https://moodle.uni-heidelberg.de/course/view.php?id={course_id}"
        response = self._session.get(course_url)
        return BeautifulSoup(response.content, "html.parser")

    def get_students(self, course_id, student_role):
        url = f'https://moodle.uni-heidelberg.de/user/index.php?id={course_id}&perpage=5000'
        response = self._session.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', attrs={'class':'flexible generaltable generalbox'}).find('tbody')
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

