import time
import sys
import openai

from enum import Enum
from typing import Optional

from gptman.contextmanagers import with_history
from gptman.prompt import read_settings
from gptman.cmd import PrefixCmd


class Backend(Enum):
    openai = 'openai'
    azure = 'azure'


def get_client(settings=None):
    settings = settings or read_settings()

    backend = Backend[settings.get('gptman', {}).get('backend', 'openai')]

    kwargs = {'api_key': settings[backend.value]['api_key']}

    if backend == Backend.openai:
        client_class = openai.OpenAI
    elif backend == Backend.azure:
        client_class = openai.lib.azure.AzureOpenAI
        kwargs['azure_endpoint'] = settings[backend.value]['azure_endpoint']
        kwargs['api_version'] = settings[backend.value]['api_version']
        if 'azure_deployment' in settings[backend.value]:
            kwargs['azure_deployment'] = settings[backend.value]['azure_deployment']

    return client_class(**kwargs)


def update_instruction(client: openai.OpenAI, asst_id: str, **kwargs):
    return client.beta.assistants.update(asst_id, **kwargs)


def list_assistants(client: openai.OpenAI):
    paginator = client.beta.assistants.list()
    for assistant in paginator:
        yield (assistant.id, assistant.name)


def run_assistant(client: openai.OpenAI, asst_id, thread):
    print('.', end='', flush=True)
    run_obj = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=asst_id,
    )

    while True:
        if run_obj.status == 'completed':
            print('.', flush=True)
            generated_content = get_generated_content(client, thread)
            return generated_content

        time.sleep(0.5)
        print('.', end='', flush=True)


def run_shell(client: openai.OpenAI, asst_id: str):
    with with_history():
        try:
            thread = client.beta.threads.create()
            shell = AssistantShell()
            shell.client = client
            shell.assistant_id = asst_id
            shell.thread = thread

            sys.exit(shell.cmdloop())
        except KeyboardInterrupt:
            return


def get_generated_content(client: openai.OpenAI, thread):
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    message = messages.data[0]
    value = message.content[0].text.value
    return value


class AssistantShell(PrefixCmd):
    intro = 'Assistant shell'
    prompt = 'Assistant> '
    client: Optional[openai.OpenAI] = None
    assistant_id: Optional[str] = None
    thread: Optional[openai.resources.beta.threads.threads.Thread] = None

    def default(self, line):
        self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role='user',
            content=line,
        )

        generated_message = run_assistant(self.client, self.assistant_id, self.thread)
        print(generated_message)

    def do_quit(self, line):
        'Quit shell'
        return 1
