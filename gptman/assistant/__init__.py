import time
import logging

import openai

from typing import List, Optional
from gptman import exceptions as exc


logger = logging.getLogger('gptman')


def update_instruction(client: openai.OpenAI, asst_id: str, **kwargs):
    tools = kwargs.pop('tools', None)
    if tools:
        kwargs['tools'] = [{'type': tool_type} for tool_type in tools.split(' ')]

    return client.beta.assistants.update(asst_id, **kwargs)


def create_assistant(client: openai.OpenAI, **kwargs):
    return client.beta.assistants.create(**kwargs)


def list_assistants(client: openai.OpenAI):
    paginator = client.beta.assistants.list()
    for assistant in paginator:
        yield assistant


def describe_assistant(client: openai.OpenAI, asst_id: str):
    return client.beta.assistants.retrieve(assistant_id=asst_id)


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
