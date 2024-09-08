import time
import os
from contextlib import contextmanager

from openai import OpenAI
from gptman.prompt import read_settings


def get_client(settings=None):
    settings = settings or read_settings()
    api_key = settings['openai']['api_key']
    return OpenAI(api_key=api_key)


def update_instruction(client: OpenAI, asst_id: str, **kwargs):
    return client.beta.assistants.update(asst_id, **kwargs)


@contextmanager
def with_history():
    histfile = os.path.join(os.path.expanduser('~'), '.gptman_history')
    try:
        import readline
        readline.read_history_file(histfile)
        readline.set_history_length(1000)
    except (FileNotFoundError, ImportError):
        pass

    yield

    try:
        import readline
        readline.write_history_file(histfile)
    except (FileNotFoundError, ImportError):
        pass


def run_shell(client: OpenAI, asst_id: str):
    with with_history():
        thread = client.beta.threads.create()

        while True:
            content = input(f'[{asst_id}] User> ')
            if content in ['quit', 'exit']:
                return

            if not content:
                continue

            client.beta.threads.messages.create(
                thread_id=thread.id,
                role='user',
                content=content,
            )

            generated_message = run_assistant(client, asst_id, thread)
            print(f'[{asst_id}] GPT>', generated_message)


def run_assistant(client, asst_id, thread):
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


def get_generated_content(client, thread):
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    message = messages.data[0]
    value = message.content[0].text.value
    return value
