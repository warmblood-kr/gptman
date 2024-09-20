import argparse
import os
import pathlib
import logging

from gptman.main import (
    get_client,
    update_instruction,
    list_assistants,
    run_shell,
)
from gptman.prompt import read_prompt_file


def push(args):
    path = args.path or [
        filename for filename in os.listdir('.')
        if filename.endswith('.md')
    ]

    client = get_client(profile=args.profile)

    def push_prompt(path):
        data = read_prompt_file(path)
        print(f"update {path} ---> {data['name']} ({data['id']})")

        asst_id = data.pop('id')
        return update_instruction(client, asst_id, **data)

    paths = path if isinstance(path, list) else [path]
    results = [push_prompt(_path) for _path in paths]
    return results


def shell(args):
    asst_id = args.id or read_prompt_file(args.path)['id']

    client = get_client(profile=args.profile)
    run_shell(client, asst_id)


def list_asst(args):
    client = get_client(profile=args.profile)
    response = list_assistants(client)
    for asst_id, asst_name in response:
        print(f'{asst_name} [{asst_id}]')


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-v', '--verbose', required=False, action='store_true')
    argparser.add_argument('--profile', required=False, action='store')

    subparsers = argparser.add_subparsers(required=True)

    assistant_parser = subparsers.add_parser('assistant')
    assistant_subparsers = assistant_parser.add_subparsers(required=True)

    push_parser = assistant_subparsers.add_parser('push')
    push_parser.add_argument('path', nargs='?')
    push_parser.set_defaults(func=push)

    shell_parser = assistant_subparsers.add_parser('shell')
    shell_parser.set_defaults(func=shell)
    group = shell_parser.add_mutually_exclusive_group(required=True)
    group.add_argument('path', nargs='?', type=pathlib.Path)
    group.add_argument('--id')

    list_parser = assistant_subparsers.add_parser('list')
    list_parser.set_defaults(func=list_asst)

    args = argparser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    args.func(args)


if __name__ == '__main__':
    main()
