from six import StringIO

from flexp.utils import log_method

s = StringIO()


@log_method(s.write)
def log_me(to=10000):
    x = 1.0
    for _ in range(to):
        x /= 2
    print(x)


def test_annotation():
    """log_method should print into sys.err.

    Method call: test_flexp.log_me
    Arguments: args: 2, kwargs:
    Method finished: test_flexp.log_me
    """
    log_me(2)
    assert s.getvalue().startswith("Method call")
