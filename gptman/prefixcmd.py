import cmd


class PrefixCmd(cmd.Cmd):
    command_prefix = '/'

    def parseline(self, line):
        """Parse the line into a command name and a string containing
        the arguments.  Returns a tuple containing (command, args, line).
        'command' and 'args' may be None if the line couldn't be parsed.
        """
        line = line.strip()
        if not line:
            return None, None, line
        elif line[0] == '?':
            line = 'help ' + line[1:]
        elif line[0] == '!':
            if hasattr(self, 'do_shell'):
                line = 'shell ' + line[1:]
            else:
                return None, None, line
        elif line[0] == self.command_prefix:
            return self.parse_cmd_line(line, 1)
        return None, None, line

    def parse_cmd_line(self, line, prefix_length=0):
        i, n = prefix_length, len(line)
        while i < n and line[i] in self.identchars: i = i+1
        cmd, arg = line[prefix_length:i], line[i:].strip()
        return cmd, arg, line

    def emptyline(self):
        'Do nothing'
        return
