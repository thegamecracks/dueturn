import gc
import pathlib
import sys
import time
import traceback
from typing import Iterable, List, Union

from src import logs
from src.textio import (
    ColoramaCodes, cr, format_color, input_color, print_color
)

logger = logs.get_logger()


def assert_type(obj, class_or_tuple):
    """Makes sure that a given object is of a specific type(s)."""
    if not isinstance(obj, class_or_tuple):
        if isinstance(class_or_tuple, tuple):
            class_or_tuple = ' or '.join(
                n.__name__ for n in class_or_tuple)
        else:
            class_or_tuple = class_or_tuple.__name__
        raise AssertionError(
            f'Expected instance of {class_or_tuple} but received object '
            f'{obj} of class {obj.__class__.__name__}')
    return obj


def collect_and_log_garbage(log_handler=None):
    garbageCollection = gc.get_stats()
    garbageCollectionLog = '\n'.join(
        [f'Generation {n}: {repr(d)}'
         for n, d in enumerate(garbageCollection)])
    if log_handler is not None:
        logger.debug(
            'Logging garbage collection:\n' + garbageCollectionLog)
    return garbageCollectionLog


def dict_copy(dictionary):
    new = {}
    for k, v in dictionary.items():
        if isinstance(v, list):
            new[k] = list_copy(v)
        elif isinstance(v, dict):
            new[k] = dict_copy(v)
        elif hasattr(v, 'copy'):
            new[k] = v.copy()
        else:
            new[k] = v
    return new


def divi_zero(n, m, *, raiseIfZero=False, failValue=0, mode=0):
    """Division function with tweakable settings.

    Args:
        n (Real): Dividend
        m (Real): Divisor
        raiseIfZero (bool):
            If True, raise ZeroDivisionError.
            Else, return failValue.
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
        if frame.name == '<module>':
            # Bottom of the stack; stop here
            break

        msg += f'Frame {frame.name!r}\n'
        # Show only the path starting from project using instead of
        # just the full path inside frame.filename
        project_path = pathlib.Path().resolve()
        trace_path = pathlib.Path(frame.filename)
        try:
            filename = trace_path.relative_to(project_path)
        except ValueError:
            # Trace must be outside of project; use that then
            filename = trace_path

        msg += f'Within file "{filename}"\n'
        msg += f'at line number {frame.lineno}:\n'
        msg += f'   {frame.line}\n'
    msg += f'\n{exc_type.__name__}: {exc_value}'

    return msg


def input_loop_if_equals(
        message=None, repeat_message=None,
        loop_if_equals=None, break_string=None,
        input_func=input):
    """Prompt the user for a string and loop if it matches a set of strings.

    Example:
        >>> input_loop_if_equals(
        ...     message='Type your name:',
        ...     repeat_message='That name is already taken! ',
        ...     loop_if_equals=('foo', 'bar'),
        ...     break_string='exit'
        ... )
        Type your name:

    Args:
        message (str): The message to prompt.
        repeat_message (str): The message to prompt when the user
            provides an answer matching `loop_if_equals`.
        loop_if_equals (Optional[Set[str]]): If provided,
            loops the prompt using `repeat_message` when the user
            types an answer in `loop_if_equals`.
        break_string (Optional[str]): If provided, returns None
            when the user types an answer equal to this.
        input_func: The function to use when input is needed.
            Defaults to input().

    """
    def parse(ans):
        if ans == break_string:
            return None
        elif ans in loop_if_equals:
            return True
        return ans

    if repeat_message is None:
        repeat_message = message

    ans = input_func(message)

    while parse(ans) is True:
        ans = input_func(repeat_message)

    return ans


def num(x) -> Union[int, float, complex]:
    """Convert an object into either a int, float, or complex in that order."""
    try:
        if hasattr(x, 'is_integer') and not x.is_integer():
            raise ValueError
        return int(x)
    except Exception:
        try:
            return float(x)
        except Exception:
            n = complex(x)
            if n.imag == 0:
                return num(n.real)
            return complex(num(n.real), num(n.imag))


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


def input_boolean(
        message, repeat_message=None,
        true=('yes', 'y'), false=('no', 'n'),
        show_option_count=-1,
        input_func=input):
    """Prompt the user for a boolean answer.

    When prompting, input is lowered and stripped regardless of `input_func`.

    Example:
        >>> input_boolean(
        ...     message='Type {true} to confirm:',
        ...     repeat_message='Unknown answer: ',
        ...     true=('yes','y'),
        ...     false=('no', 'n'),
        ...     show_option_count=2
        ... )
        Type (yes/y) to confirm:

    Args:
        message (str): The message to prompt.
        repeat_message (str): The message to prompt when the user gives
            an invalid input.
        true (Sequence[str]): A sequence of allowed answers for True.
        false (Optional[Sequence[str]]): A sequence of allowed answers
            for False. Can be set to None to return False if the user
            does not type anything matching `true`.
        show_option_count (int):
            If greater than 0,
            substitutes {true} and {false} within `message` and
            `repeat_message` to show the allowed answers for True and False,
            up to `show_option_count`.
            If less than 0, does the same as above except it shows all options.
            If exactly 0, {true} and {false} are not substituted.
        input_func: The function to use when input is needed.
            Defaults to input().

    """
    def parse(ans):
        if ans in true:
            return True
        elif false is None:
            return False
        elif ans in false:
            return False
        return None

    if show_option_count != 0:
        if show_option_count > 0:
            true_str = '({})'.format('/'.join(true[:show_option_count]))
            false_str = '({})'.format('/'.join(false[:show_option_count])) \
                        if false is not None else ''
        else:
            true_str = f"({'/'.join(true)})"
            false_str = f"({'/'.join(false)})" \
                        if false is not None else ''
        # Format colors and true/false options
        message = format_color(
            message,
            namespace={'true': true_str, 'false': false_str}
        )
        if repeat_message is None:
            repeat_message = message
        else:
            repeat_message = format_color(
                repeat_message,
                namespace={'true': true_str, 'false': false_str}
            )
    else:
        message = format_color(message)
        if repeat_message is None:
            repeat_message = message
        else:
            repeat_message = format_color(repeat_message)

    # Get input
    ans = input_func(message).lower().strip()

    while (meaning := parse(ans)) is None:
        ans = input_func(repeat_message).lower().strip()

    return meaning


def list_copy(items: Iterable) -> List:
    """Run the 'copy' method on each item if available and return a list."""
    return [item.copy() if hasattr(item, 'copy') else item
            for item in items]
