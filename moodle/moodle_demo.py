import util.config

from moodle.api import MoodleSession

moodle_account = util.config.load_config("../account_data.json").moodle

with MoodleSession(account=moodle_account) as session:
    course_page = session.get_course_page(course_id=2239)
    print(course_page)