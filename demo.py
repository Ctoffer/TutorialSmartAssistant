from data.storage import InteractiveDataStorage
from moodle.api import MoodleSession
from muesli.api import MuesliSession
from util.feedback import FeedbackPolisher

abs_path = "C:/Users/chris/Documents/Uni/SoSe20/IAD/Übungsblätter/Übungsblatt_1/04_Korrektur/Ahmet-Örün_David-Türck_Gediminas-Marcinkevicius_ex01"
storage = InteractiveDataStorage()
with MuesliSession(account=storage.muesli_account) as muesli:
    with MoodleSession(account=storage.moodle_account) as moodle:
        storage.init_data(muesli, moodle)

        analyzer = FeedbackPolisher(
            storage,
            abs_path
        )

