'''gptman is a Python package designed to streamline the management of OpenAI ChatGPT Assistant API prompts using local Markdown files. With gptman, developers can easily update assistant configurations and manage prompts through simple command-line interface (CLI) commands.
'''

from importlib import resources

with resources.files('gptman').joinpath('VERSION').open() as f:
    __version__ = f.read().strip()
