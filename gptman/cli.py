import argparse
import os

from gptman.main import push_prompt


def push(args):
    path = args.path or [
        filename for filename in os.listdir('.')
        if filename.endswith('.md')
    ]

    if isinstance(path, list):
        for _path in path:
            push_prompt(_path)
    else:
        push_prompt(path)


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
