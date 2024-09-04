from gptman.prompt import (
    read_prompt_file,
    parse_markdown_with_preamble,
)


def test_read_prompt_file():
    assert read_prompt_file('tests/fixture/test_prompt.md') == {
        'id': 'test-file-id',
        'instructions': 'Test prompt\n'
    }


def test_parse_markdown_with_preamble():
    text = '''---
id: test-id
---
Test prompt
'''
    assert parse_markdown_with_preamble(text) == {
        'id': 'test-id',
        'instructions': 'Test prompt\n',
    }
