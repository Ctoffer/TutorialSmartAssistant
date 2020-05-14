from data.storage import InteractiveDataStorage
from moodle.api import MoodleSession
from muesli.api import MuesliSession
from util.console import ConsoleFormatter

storage = InteractiveDataStorage()
with MoodleSession(account=storage.moodle_account) as moodle:
    with MuesliSession(account=storage.muesli_account) as muesli:
        storage.init_data(muesli=muesli, moodle=moodle)
        storage.download_submissions_of_my_students(moodle, 1, ConsoleFormatter())
