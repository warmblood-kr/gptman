import argparse
import logging

from gptman.cli import assistant


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-v', '--verbose', required=False, action='store_true')
    argparser.add_argument('--profile', required=False, action='store')

    subparsers = argparser.add_subparsers(required=True)

    assistant_parser = subparsers.add_parser('assistant')
    assistant_subparsers = assistant_parser.add_subparsers(required=True)
    assistant.setup_cli(assistant_subparsers)

    args = argparser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    args.func(args)


if __name__ == '__main__':
    main()
