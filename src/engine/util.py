import sys
import time
import traceback
from typing import Iterable, List

from src import logs

logger = logs.get_logger()


def divi_zero(n, m, raiseIfZero=False, failValue=0, mode=0):
    """Division function with tweakable settings.

    Args:
        n (Real): Dividend
        m (Real): Divisor
        raiseIfZero (bool):
            If True, return failValue if the denominator is 0.
        failValue (Real):
            Value to return if n == 0 or m == 0 and not raiseIfZero.
        mode (Literal[-1, 0, 1]):
            0 for normal division
            -1 for floor division
            1 for ceil division

    """
    if n == 0:
        return failValue
    if m == 0:
        if raiseIfZero:
            raise ZeroDivisionError(f'{n!r} / {m!r}')
        return failValue

    if mode == 0:
        return n / m
    elif mode == -1:
        return n // m
    elif mode == 1:
        return (n + m - 1) // m
    else:
        raise ValueError(f'Invalid mode parameter ({mode})')


def exception_message(
        exc_type=None, exc_value=None, exc_traceback=None,
        header: str = '', log_handler=None) -> str:
    """Create a message out of the last exception handled by try/except.

    Args:
        header (Optional[str]): The header to place above the message.
        log_handler (Optional): The logger to run the exception() method on.

    Returns:
        str: The string containing the exception message.

    """
    if exc_type is None and exc_value is None and exc_traceback is None:
        exc_type, exc_value, exc_traceback = sys.exc_info()
    elif exc_type is None or exc_value is None or exc_traceback is None:
        raise ValueError('An exception type/value/traceback was passed '
                         'but is missing the other values')

    # Header message with padded border
    msg = ''
    if header:
        msg = '{:=^{length}}\n'.format(
            header, length=len(header) * 2 + len(header) % 2)

    if log_handler is not None:
        # Log the exception; doesn't require creating a message
        logger.exception(msg)

    # Create the message to return, containing the traceback and exception
    for frame in traceback.extract_tb(exc_traceback):
        msg += f'Frame {frame.name!r}\n'
        # Show only the file name instead of the full location
        filename = frame.filename[::-1]
        filename = filename[:filename.find('\\') + 1] + '..'
        filename = filename[::-1]

        msg += f'Within file "{filename}"\n'
        msg += f'at line number {frame.lineno}:\n'
        msg += f'   {frame.line}\n'
    msg += f'\n{exc_type.__name__}: {exc_value}'

    return msg


def pause(sleep=None, printNewline=0):
    """When not given a number, will block current thread with input().
    Otherwise, will use time.sleep() for the specified time.

    Args:
        sleep (Optional[RealNum]): The time to sleep for.
            If None, will call input().
        printNewline (Literal[0, 1, 2]):
            When using time.sleep (sleep is not None),
            if 1, then a newline is printed before calling time.sleep(sleep);
            if 2, then it is printed after the call.
            For no newline, set to 0.

    """
    if sleep is None:
        input()
    else:
        if printNewline == 1:
            print()
        time.sleep(sleep)
        if printNewline == 2:
            print()


def plural(n, pluralString='s', naturalOnly=False):
    """Return a plural suffix if a number should be read as plural.

    Args:
        n (RealNum): The number to check.
        pluralString (str): The plural suffix to return
            if `n` should be a pluralized quantity.
        naturalOnly (bool): If True, return plural if n != 1.
            Otherwise, return plural if abs(n) != 1.

    Returns:
        str

    """
    if naturalOnly and n == 1:
        return ''
    elif abs(n) == 1:
        return ''
    return pluralString


def list_copy(items: Iterable) -> List:
    """Run the 'copy' method on each item if available and return a list."""
    return [item.copy() if hasattr(item, 'copy') else item
            for item in items]
