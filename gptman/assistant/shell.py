import datetime
import logging

import openai

from pathlib import Path
from typing import Optional

from openai.resources.beta.threads.threads import Thread

from gptman.contextmanagers import with_history
from gptman.prefixcmd import PrefixCmd
from gptman.assistant import (
    run_assistant,
    attach_file,
    send_message,
    list_files,
    delete_file,
)

logger = logging.getLogger('gptman')


def run_shell(client: openai.OpenAI, asst_id: str):
    with with_history():
        try:
            shell = AssistantShell(client, asst_id)
            shell.cmdloop()
        except KeyboardInterrupt:
            return


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
    thread: Optional[Thread]

    def __init__(self, client: openai.OpenAI, assistant_id: Optional[str], **kwargs):
        self.client = client
        self.assistant_id = assistant_id
        self.renew_pipeline = False
        self.debug_mode = False
        self.new_thread()

        super().__init__(**kwargs)

    def new_thread(self):
        self.thread = self.client.beta.threads.create()

    def default(self, line):
        asst_ids = self.assistant_id if isinstance(self.assistant_id, (list, tuple)) else [self.assistant_id]

        for asst_id in asst_ids:
            if self.do_set_renew:
                self.new_thread()
            self.client.beta.threads.messages.create(
                thread_id=self.thread.id,
                role='user',
                content=line,
            )

            print(f'Querying thread to assistant {asst_id}...')
            line = run_assistant(self.client, asst_id, self.thread)
            if self.debug_mode:
                print('--- START DEBUG MESSAGE ---')
                print(line)
                print('---   END DEBUG MESSAGE ---')
        print(line)

    def do_set_debug(self, arg):
        'Whether renew or keep during pipeline'
        self.debug_mode = arg in ['true', 'True', 'yes', 'y', 't']

    def do_set_renew(self, arg):
        'Whether renew or keep during pipeline'
        self.renew_pipeline = arg in ['true', 'True', 'yes', 'y', 't']

    def do_assistant(self, arg):
        'Set assistant ID. It can be ID list to use prompt chaining.'
        if arg:
            self.assistant_id = [s.strip() for s in arg.split()]

    def do_load(self, arg):
        'Load script text and query it to assistant'
        path = Path(arg)
        if not path.exists():
            print(f'File {arg} is not exists')
            return
        content = path.read_text()
        self.default(content)

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
