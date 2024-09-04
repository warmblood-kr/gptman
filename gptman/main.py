import tomllib

from openai import OpenAI
from gptman.exceptions import PreambleNotFound


def get_client(settings=None):
    settings = settings or read_settings()
    api_key = settings['openai']['api_key']
    return OpenAI(api_key=api_key)


def read_settings():
    with open("gptman.toml", "rb") as f:
        return tomllib.load(f)


def update_instruction(client, asst_id, **kwargs):
    return client.beta.assistants.update(asst_id, **kwargs)


def run_shell(client, asst_id):
    print(asst_id)


def read_prompt_file(path):
    with open(path) as fin:
        body = fin.read()
        return parse_markdown_with_preamble(body)


def parse_markdown_with_preamble(text):
    lines = text.split('\n')
    if not lines[0].startswith('---'):
        raise PreambleNotFound()

    data = {}

    for idx, line in enumerate(lines[1:], 1):
        if line.startswith('---'):
            data['instructions'] = '\n'.join(lines[idx+1:])
            return data

        k, v = parse_preamble_data(line)
        data[k] = v

    raise PreambleNotFound()


def parse_preamble_data(line):
    k, v = line.split(':', 1)
    return k, v.strip()
