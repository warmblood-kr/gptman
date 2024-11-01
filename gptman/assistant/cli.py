import os

from pathlib import Path

from tabulate import tabulate

from gptman.main import get_client
from gptman.assistant import (
    update_instruction,
    list_assistants,
    describe_assistant,
    create_assistant,
)
from gptman.assistant.shell import run_shell

from gptman.assistant.prompt import (
    read_prompt_file,
    write_prompt_file,
)


def push(args):
    path = args.path or [
        filename
        for filename in os.listdir('.')
        if filename.endswith('.md')
    ]

    client = get_client(profile=args.profile)

    def push_prompt(path):
        data = read_prompt_file(path)
        print(f"update {path} ---> {data['name']} ({data['id']})")

        asst_id = data.pop('id')

        if asst_id:
            return update_instruction(client, asst_id, **data)
        else:
            asst = create_assistant(client, **data)
            data_with_id = {**data, 'id': asst.id}
            write_prompt_file(path, data_with_id)

    paths = path if isinstance(path, list) else [path]
    results = [push_prompt(_path) for _path in paths]
    return results


def pull(args):
    prompt_filenames = [
        name
        for name in os.listdir('.')
        if name.endswith('.md')
    ]

    asst_id_to_filename = {
        read_prompt_file(filename).get('id'): filename
        for filename in prompt_filenames
    }

    def extract_data_from_assistant(asst):
        return {
            'id': asst.id,
            'name': asst.name,
            'model': asst.model,
            'instructions': asst.instructions,
        }

    def update_or_create_prompt(data):
        filename = asst_id_to_filename.get(data['id']) \
            or '{}.md'.format(data['name'] or data['id'])

        write_prompt_file(filename, data)

    client = get_client(profile=args.profile)
    assistants = list_assistants(client)
    asst_data_list = [
        extract_data_from_assistant(asst)
        for asst in assistants
    ]
    return [
        update_or_create_prompt(asst_data)
        for asst_data in asst_data_list
    ]


def shell(args):
    asst_id = args.id or read_prompt_file(args.path)['id']

    client = get_client(profile=args.profile)
    run_shell(client, asst_id)


def list_asst(args):
    client = get_client(profile=args.profile)

    data = [('name', 'id')]
    data += [
        (assistant.name, assistant.id)
        for assistant in list_assistants(client)
    ]

    print(tabulate(data, headers="firstrow"))


def describe(args):
    asst_id = args.id or read_prompt_file(args.path)['id']

    client = get_client()
    response = describe_assistant(client, asst_id)
    for asst_id, asst_name in response:
        print(f'{asst_name} [{asst_id}]')


def setup_cli(assistant_subparsers):
    push_parser = assistant_subparsers.add_parser('push')
    push_parser.add_argument('path', nargs='?')
    push_parser.set_defaults(func=push)

    pull_parser = assistant_subparsers.add_parser('pull')
    pull_parser.set_defaults(func=pull)

    shell_parser = assistant_subparsers.add_parser('shell')
    shell_parser.set_defaults(func=shell)
    group = shell_parser.add_mutually_exclusive_group(required=True)
    group.add_argument('path', nargs='?', type=Path)
    group.add_argument('--id')

    list_parser = assistant_subparsers.add_parser('list')
    list_parser.add_argument('-l', '--long', action='store_true')
    list_parser.set_defaults(func=list_asst)

    describe_parser = assistant_subparsers.add_parser('describe')
    group = describe_parser.add_mutually_exclusive_group(required=True)
    group.add_argument('path', nargs='?', type=Path)
    group.add_argument('--id')
    describe_parser.set_defaults(func=describe)
