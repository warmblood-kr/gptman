import time
import json
from openai import OpenAI
from gptman.prompt import read_settings


def get_client(settings=None):
    settings = settings or read_settings()
    api_key = settings['openai']['api_key']
    return OpenAI(api_key=api_key)


def update_instruction(client: OpenAI, asst_id: str, **kwargs):
    return client.beta.assistants.update(asst_id, **kwargs)


def run_shell(client: OpenAI, asst_id: str):
    thread = client.beta.threads.create()

    while True:
        content = input(f'[{asst_id}] User > ')
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
        print(f'[{asst_id}] GPT >', generated_message)


def run_assistant(client, asst_id, thread):
    run_obj = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=asst_id,
    )

    while True:
        if run_obj.status == 'completed':
            generated_content = get_generated_content(client, thread)
            return generated_content

        time.sleep(0.5)


def get_generated_content(client, thread):
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    message = messages.data[0]
    value = message.content[0].text.value

    try:
        json_value = json.loads(value)
        generated_content = json_value['values'] or json_value['error']
        return generated_content
    except (json.JSONDecodeError, KeyError):
        return value
