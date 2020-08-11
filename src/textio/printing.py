import time

__all__ = [
    'print_sleep',
    'print_sleep_multiline'
]


def print_sleep(*value, sleep=0, sleep_after=True, **kwargs):
    """Call the print function, sleeping before/after.

    Args:
        value: The messages to print. Acts in the same way as print().
        sleep (Union[int, float]): The amount of time to sleep.
        sleep_after (bool): Chooses whether to sleep before or after
            printing the message.
        sep
        end
        file
        flush

    """
    if not sleep_after:
        time.sleep(sleep)
    print(*value, **kwargs)
    if sleep_after:
        time.sleep(sleep)


def print_sleep_multiline(*value, sep='\n', end='\n', **kwargs):
    """Sleep before/after every newline in the given value(s)
    using `print_sleep`.

    `sep` default has been changed to '\n', allowing comma separated lines.

    Use keyword arguments to provide parameters to `print_sleep`.

    """
    values = sep.join([str(a) for a in value])

    for line in values.split('\n'):
        print_sleep(line, end='', **kwargs)
        if len(values) != 1:
            print(end=sep)
    print(end=end)
