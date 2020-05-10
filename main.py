from assistance.smart_assistant import SmartAssistant


def main():
    assistant = SmartAssistant()
    assistant.hello()
    while assistant.ready:
        assistant.execute_cycle()


if __name__ == '__main__':
    main()
