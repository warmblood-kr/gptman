import os
from contextlib import contextmanager


@contextmanager
def with_history(filename=None, write_history=False):  # pragma: no cover
    histfile = filename or os.path.join(os.path.expanduser('~'), '.gptman_history')
    try:
        import readline
        readline.read_history_file(histfile)
        readline.set_history_length(1000)
    except (FileNotFoundError, ImportError):
        pass

    yield

    try:
        import readline
        if write_history:
            readline.write_history_file(histfile)
    except (FileNotFoundError, ImportError):
        pass
