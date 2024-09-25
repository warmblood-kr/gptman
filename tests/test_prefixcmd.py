from gptman.prefixcmd import PrefixCmd


class MockCmd(PrefixCmd):
    def do_shell(self, args):
        return


class TestPrefixCmd:
    def test_parse_cmd_line(self):
        cmd = PrefixCmd()

        assert cmd.parseline('This is a normal line') == (None, None, 'This is a normal line')
        assert cmd.parseline('/attach This is a normal line') == ('attach', 'This is a normal line', '/attach This is a normal line')
        assert cmd.parseline('attach This is a normal line') == (None, None, 'attach This is a normal line')
        assert cmd.parseline('') == (None, None, '')
        assert cmd.parseline('?') == (None, None, 'help ')
        assert cmd.parseline('!') == (None, None, '!')

    def test_with_shell(self):
        cmd = MockCmd()
        assert cmd.parseline('!') == (None, None, 'shell ')
