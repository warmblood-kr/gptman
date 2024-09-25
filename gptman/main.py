import time
import openai
import datetime
import logging

from pathlib import Path
from enum import Enum
from typing import Optional

from gptman import exceptions as exc
from gptman.contextmanagers import with_history
from gptman.prompt import read_settings
from gptman.prefixcmd import PrefixCmd

logger = logging.getLogger('gptman')


class Backend(Enum):
    openai = 'openai'
    azure = 'azure'


def get_client(settings=None, profile=None):
    settings = settings or read_settings()

    profile_settings = settings.get('profile', {}).get(profile, {}) if profile \
        else settings.get('gptman', {})

    backend = Backend[profile_settings.get('backend', 'openai')]

    kwargs = {'api_key': profile_settings['api_key']}

    if backend == Backend.openai:
        client_class = openai.OpenAI
    elif backend == Backend.azure:
        client_class = openai.lib.azure.AzureOpenAI
        kwargs['azure_endpoint'] = profile_settings['azure_endpoint']
        kwargs['api_version'] = profile_settings['api_version']
        if 'azure_deployment' in profile_settings:
            kwargs['azure_deployment'] = profile_settings['azure_deployment']

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


def run_assistant(client: openai.OpenAI, asst_id, thread, timeout=60):
    print('.', end='', flush=True)
    run_obj = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=asst_id,
    )

    interval = 1
    for _ in range(int(timeout / interval)):
        logger.debug(run_obj)
        if run_obj.status == 'completed':
            print('.', flush=True)
            generated_content = get_generated_content(client, thread)
            logger.debug(generated_content)
            return generated_content

        time.sleep(interval)
        print('.', end='', flush=True)

    raise exc.RequestTimeout(run_obj)


def run_shell(client: openai.OpenAI, asst_id: str):
    with with_history():
        try:
            thread = client.beta.threads.create()
            shell = AssistantShell(client, asst_id, thread)
            shell.cmdloop()
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


def send_message(client: openai.OpenAI, assistant_id, thread, content, attachments=None, file_ids=None):
    kwargs = {
        'thread_id': thread.id,
        'role': 'user',
        'content': content,
    }
    if attachments:
        kwargs['attachments'] = attachments

    if file_ids:
        kwargs['file_ids'] = file_ids

    message = client.beta.threads.messages.create(**kwargs)
    logger.debug(message)

    generated_message = run_assistant(client, assistant_id, thread)
    return generated_message


def attach_file(client: openai.OpenAI, path, purpose='assistants'):
    with open(path, 'rb') as fin:
        message_file = client.files.create(
            file=fin, purpose=purpose
        )
        logger.debug(message_file)
        return message_file


def delete_file(client: openai.OpenAI, file_id):
    return client.files.delete(file_id)


def list_files(client: openai.OpenAI):
    return client.files.list()


SUPPORTED_FILES = [
    '.c', '.cpp', '.cs', '.css',
    '.doc', '.docx', '.html',
    '.java', '.js', '.json',
    '.md',
    '.pdf', '.php', '.pptx', '.py',
    '.rb', '.sh', '.tex', '.ts', '.txt'
]


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

    def do_image(self, arg):
        '''Upload an image file.\n/image <filepath>'''
        if not arg:
            print('Filename should be provided')
            return

        path = Path(arg)

        if not path.exists():
            print(f'File {arg} is not exists')
            return

        if path.suffix not in ['.png']:
            print(f'{path.suffix} file is not supported')
            return

        message_file = attach_file(self.client, arg, purpose='vision')
        print(f'Image is uploaded: {message_file}')

        # OpenAI playground assistant UI do this
        content = [
            {'type': 'image_file', 'image_file': {'file_id': message_file.id}}
        ]
        result = send_message(self.client, self.assistant_id, self.thread, content)
        print('File is attached to the thread.')
        print(result)

    def do_file(self, arg):
        '''Upload a file.\n/file <filepath>'''

        if arg.strip() == 'list':
            self.sub_do_file_list()
            return

        if arg.startswith('delete'):
            file_id = arg.split(' ', 1)
            self.sub_do_file_delete(file_id)
            return

        if arg.startswith('status'):
            file_id = arg.split(' ', 1)
            self.sub_do_file_status(file_id)
            return

        self.sub_do_file_upload(arg)

    def sub_do_file_list(self):
        for file_obj in list_files(self.client):
            created_at = datetime.datetime.fromtimestamp(file_obj.created_at)
            print(f'{file_obj.filename} [{file_obj.id}, {created_at}]')

    def sub_do_file_delete(self, file_id):
        print(delete_file(self.client, file_id))

    def sub_do_file_upload(self, arg):
        if not arg:
            print('Filename should be provided')
            return

        path = Path(arg)

        if not path.exists():
            print(f'File {arg} is not exists')
            return

        if path.suffix not in SUPPORTED_FILES:
            print(f'{path.suffix} file is not supported')
            return

        message_file = attach_file(self.client, arg)
        print(f'File is uploaded: {message_file.filename} ({message_file.id})')

        # TODO: link file and thread/message

        content = 'Here is a file you can refer.'
        kwargs = {}
        kwargs['attachments'] = [
            {'file_id': message_file.id, 'tools': [{'type': 'file_search'}]},
        ]

        message = send_message(self.client, self.assistant_id, self.thread, content, **kwargs)
        logger.debug(message)
        print('File is attached to the thread.')

    def sub_do_file_status(self, file_id):
        file_info = self.client.files.retrieve(file_id)
        print(file_info)
