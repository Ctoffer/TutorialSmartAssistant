from time import sleep

from assistance.smart_assistant import SmartAssistant
from data.storage import InteractiveDataStorage
from moodle.api import MoodleSession
from muesli.api import MuesliSession
from util import console


def main():
    storage = InteractiveDataStorage()

    with MuesliSession(account=storage.muesli_account) as muesli:
        with MoodleSession(account=storage.moodle_account) as moodle:
            print('┌───────────────────────────────────────────────────────────────────────────────────────┐')
            print('│                                  Initializing Storage                                 │')
            print('└───────────────────────────────────────────────────────────────────────────────────────┘')
            storage.init_data(muesli, moodle)
            for i in range(5,-1,-1):
                print(f'Launching ASA in {i}s', end='\r')
                sleep(1)
            console.clear()

            assistant = SmartAssistant(storage, muesli, moodle)
            while assistant.is_ready():
                assistant.execute_cycle()




if __name__ == '__main__':
    main()