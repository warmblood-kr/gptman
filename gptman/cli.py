import argparse
import os
import pathlib

from gptman.main import (
    get_client,
    read_prompt_file,
    run_shell,
    update_instruction,
)


def push(args):
    path = args.path or [
        filename for filename in os.listdir('.')
        if filename.endswith('.md')
    ]

    client = get_client()

    def push_prompt(path):
        data = read_prompt_file(path)
        print(f"update {path} ---> {data['name']} ({data['id']})")

        asst_id = data.pop('id')
        return update_instruction(client, asst_id, **data)

    if isinstance(path, list):
        for _path in path:
            push_prompt(_path)
    else:
        push_prompt(path)


def shell(args):
    asst_id = args.id or read_prompt_file(args.path)['id']
    run_shell(asst_id)


def main():
    argparser = argparse.ArgumentParser()
    subparsers = argparser.add_subparsers(required=True)

    push_parser = subparsers.add_parser('push')
    push_parser.add_argument('path', nargs='?')
    push_parser.set_defaults(func=push)

    shell_parser = subparsers.add_parser('shell')
    shell_parser.set_defaults(func=shell)
    group = shell_parser.add_mutually_exclusive_group(required=True)
    group.add_argument('path', nargs='?', type=pathlib.Path)
    group.add_argument('--id')

    args = argparser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
