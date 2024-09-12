from gptman.cmd import PrefixCmd


def test_parse_cmd_line():
    cmd = PrefixCmd()

    assert cmd.parseline('This is a normal line') == (None, None, 'This is a normal line')
    assert cmd.parseline('/attach This is a normal line') == ('attach', 'This is a normal line', '/attach This is a normal line')
    assert cmd.parseline('attach This is a normal line') == (None, None, 'attach This is a normal line')
