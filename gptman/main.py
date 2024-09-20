import time
import sys
import openai

from pathlib import Path
from enum import Enum
from typing import Optional

from gptman.contextmanagers import with_history
from gptman.prompt import read_settings
from gptman.prefixcmd import PrefixCmd


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
    tools = kwargs.pop('tools', None)
    if tools:
        kwargs['tools'] = [{'type': tool_type} for tool_type in tools.split(' ')]

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
            shell = AssistantShell(client, asst_id, thread)
            sys.exit(shell.cmdloop())
        except KeyboardInterrupt:
            return


def get_generated_content(client: openai.OpenAI, thread):
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    last_message = messages.data[0]

    MAP = {
        'ImageFileContentBlock': lambda v: v.image_file.file_id,
        'ImageURLContentBlock': lambda v: v.image_url.url,
        'TextContentBlock': lambda v: v.text.value,
    }

    value = '\n\n'.join([
        MAP[type(content).__name__](content)
        for content in last_message.content
    ])
    return value


def send_message(client: openai.OpenAI, assistant_id, thread, content):
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role='user',
        content=content,
    )

    generated_message = run_assistant(client, assistant_id, thread)
    return generated_message


def attach_file(client: openai.OpenAI, path, purpose='assistants'):
    with open(path, 'rb') as fin:
        message_file = client.files.create(
            file=fin, purpose='assistants'
        )
        return message_file


class AssistantShell(PrefixCmd):
    intro = 'Assistant shell'
    prompt = 'Assistant> '
    client: Optional[openai.OpenAI]
    assistant_id: Optional[str]
    thread: Optional[openai.resources.beta.threads.threads.Thread]

    def __init__(self, client: openai.OpenAI, assistant_id: str,
                 thread: openai.resources.beta.threads.threads.Thread,
                 **kwargs):
        self.client = client
        self.assistant_id = assistant_id
        self.thread = thread
        super().__init__(**kwargs)

    def default(self, line):
        self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role='user',
            content=line,
        )

        generated_message = run_assistant(self.client, self.assistant_id, self.thread)
        print(generated_message)

    def do_quit(self, arg):
        'Quit shell'
        return 1

    def do_attach(self, arg):
        '''Attach file.\n/attach <filepath>'''
        if not arg:
            print('Filename should be provided')
            return

        if not Path(arg).exists():
            print(f'File {arg} is not exists')
            return

        message_file = attach_file(self.client, arg)
        print(f'File is uploaded: {message_file}')

        # TODO: link file and thread/message

        content = 'Here is a file you can refer.'
        send_message(self.client, self.assistant_id, self.thread, content)
        print('File is attached to the thread.')
