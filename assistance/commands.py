def normalize_string(string):
    if string.startswith('"') and string.endswith('"'):
        string = string[1:-1]
    return string


def parse_command(command):
    if ' ' in command:
        protected = False
        buffer = list()
        parts = list()
        for i, c in enumerate(command):
            if c == '"':
                protected = not protected

            if c == " " and not protected:
                parts.append(''.join(buffer))
                buffer.clear()
            else:
                buffer.append(c)

        if len(buffer) > 0:
            parts.append(''.join(buffer))

        name, args = parts[0], parts[1:]
    else:
        name, args = command, list()

    return name, args


class CommandRegister:
    def __init__(self):
        self._commands = dict()
        self._listed_commands = list()
        self._aliases = dict()

    @property
    def commands(self):
        return self._commands.values()

    def register_command(self, command):
        self._listed_commands = command.name
        self._aliases.update({alias: command.name for alias in command.aliases})
        self._commands[command.name] = command

    def get_command(self, name):
        if name in self._aliases:
            name = self._aliases[name]

        if name not in self._commands:
            raise KeyError(f"Unknown command name or alias: '{name}'.")

        return self._commands[name]
