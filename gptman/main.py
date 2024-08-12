import tomllib
import argparse
import os

from openai import OpenAI


def push(args):
    path = args.path or [filename for filename in os.listdir('.')\
                         if filename.endswith('.md')]

    if isinstance(path, list):
        for _path in path:
            push_prompt(_path)
    else:
        push_prompt(path)


def push_prompt(path=None):
    settings = read_settings()
    data = read_prompt_file(path)
    kwargs = {
        'api_key': settings['openai']['api_key'],
        **data
    }
    print(f"update {path} ---> {data['name']} ({data['id']})")
    update_instruction(**kwargs)


def read_settings():
    with open("gptman.toml", "rb") as f:
        return tomllib.load(f)


def update_instruction(api_key, **kwargs):
    client = OpenAI(api_key=api_key)
    id = kwargs.pop('id')
    return client.beta.assistants.update(id, **kwargs)


def read_prompt_file(path):
    with open(path) as fin:
        body = fin.read()

        return parse_markdown_with_preamble(body)


def parse_markdown_with_preamble(text):
    lines = text.split('\n')
    idx = 0
    assert lines[idx] == '---'
    data = {}

    while True:
        idx += 1

        if lines[idx] == '---':
            data['instructions'] = '\n'.join(lines[idx+1:])
            return data

        k, v = parse_preamble_data(lines[idx])
        data[k] = v


def parse_preamble_data(line):
    k, v = line.split(':', 1)
    return k, v.strip()


def main():
    argparser = argparse.ArgumentParser()
    subparsers = argparser.add_subparsers()
    push_parser = subparsers.add_parser('push')
    push_parser.add_argument('path', nargs='?')
    push_parser.set_defaults(func=push)

    args = argparser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()

