import logging
import pytest

from gptman import exceptions as exc
from gptman.assistant.prompt import (
    read_prompt_file,
    parse_markdown_with_preamble,
)
from gptman.main import read_settings


def test_read_settings():
    assert not read_settings(['test_setting.txt'])


def test_read_prompt_file():
    assert read_prompt_file('tests/fixture/test_prompt.md') == {
        'id': 'test-file-id',
        'instructions': 'Test prompt\n'
    }


class TestParseMarkdownWithPreamble:
    def test_with_preamble(self):
        text = '''---
id: test-id
---
Test prompt
'''
        assert parse_markdown_with_preamble(text) == {
            'id': 'test-id',
            'instructions': 'Test prompt\n',
        }

    def test_without_open_preamble(self):
        text = '''
id: test-id
---
Test prompt
'''

        with pytest.raises(exc.PreambleNotFound):
            parse_markdown_with_preamble(text) == {
                'id': 'test-id',
                'instructions': 'Test prompt\n',
            }

    def test_without_close_preamble(self):
        text = '''---
id: test-id
'''

        with pytest.raises(exc.PreambleNotFound):
            parse_markdown_with_preamble(text) == {
                'id': 'test-id',
                'instructions': 'Test prompt\n',
            }
