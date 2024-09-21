from gptman.contextmanagers import with_history


def test_with_history():
    with with_history(write_history=False):
        assert True
