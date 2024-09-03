import tomllib

from openai import OpenAI


def get_client(settings=None):
    settings = settings or read_settings()
    api_key = settings['openai']['api_key']
    return OpenAI(api_key=api_key)


def push_prompt(path):
    settings = read_settings()
    client = get_client(settings)

    data = read_prompt_file(path)
    print(f"update {path} ---> {data['name']} ({data['id']})")
    return update_instruction(client, **data)


def read_settings():
    with open("gptman.toml", "rb") as f:
        return tomllib.load(f)


def update_instruction(client, **kwargs):
    id = kwargs.pop('id')
    return client.beta.assistants.update(id, **kwargs)


def read_prompt_file(path):
    with open(path) as fin:
        body = fin.read()
        return parse_markdown_with_preamble(body)


def parse_markdown_with_preamble(text):
    lines = text.split('\n')
    assert lines[0].startswith('---')
    data = {}

    for idx, line in enumerate(lines[1:], 1):
        if line.startswith('---'):
            data['instructions'] = '\n'.join(lines[idx+1:])
            return data

        k, v = parse_preamble_data(line)
        data[k] = v


def parse_preamble_data(line):
    k, v = line.split(':', 1)
    return k, v.strip()
