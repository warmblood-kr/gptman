import os
from contextlib import contextmanager


@contextmanager
def with_history():
    histfile = os.path.join(os.path.expanduser('~'), '.gptman_history')
    try:
        import readline
        readline.read_history_file(histfile)
        readline.set_history_length(1000)
    except (FileNotFoundError, ImportError):
        pass

    yield

    try:
        import readline
        readline.write_history_file(histfile)
    except (FileNotFoundError, ImportError):
        pass
