import abc

from gptman.contextmanagers import with_history
from gptman.main import run_assistant


def run_shell(client, asst_id: str):
    with with_history():
        thread = client.beta.threads.create()
        context = {}

        try:
            while True:
                content = input(f'[{asst_id}] User> ')
                command = Command.select_command(content)
                command.execute(client, asst_id, thread, context, content)
        except QuitShellSignal:
            return


class QuitShellSignal(Exception):
    'QuitShellSignal'


class Command:
    special = False

    @abc.abstractmethod
    def execute(self, client, asst_id, thread, context, content):
        'execute method'

    @abc.abstractmethod
    def match(self, content):
        'match method'

    @classmethod
    def select_command(cls, content):
        special_commands = [c() for c in Command.__subclasses__() if c.special]

        for cmd in special_commands:
            if cmd.match(content):
                return cmd

        normal_commands = [c() for c in Command.__subclasses__() if not c.special]
        for cmd in normal_commands:
            if cmd.match(content):
                return cmd


class QuitCommand(Command):
    special = True

    def match(self, content):
        return content and content.strip() in ['quit', 'exit', 'q']

    def execute(self, client, asst_id, thread, context, content):
        raise QuitShellSignal()


class NullCommand(Command):
    special = True

    def match(self, content):
        return not content or content.strip() == ''

    def execute(self, client, asst_id, thread, context, content):
        return


class AskCommand(Command):
    def match(self, content):
        return True

    def execute(self, client, asst_id, thread, context, content):
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role='user',
            content=content,
        )

        generated_message = run_assistant(client, asst_id, thread)
        print(f'[{asst_id}] GPT>', generated_message)
