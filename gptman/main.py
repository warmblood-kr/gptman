from openai import OpenAI
from gptman.prompt import read_settings


def get_client(settings=None):
    settings = settings or read_settings()
    api_key = settings['openai']['api_key']
    return OpenAI(api_key=api_key)


def update_instruction(client, asst_id, **kwargs):
    return client.beta.assistants.update(asst_id, **kwargs)


def run_shell(client, asst_id):
    print(asst_id)
