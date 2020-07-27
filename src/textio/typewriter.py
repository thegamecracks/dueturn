"""Provides functions for typewriter I/O."""
import functools
import time

__all__ = [
    # Get a specific choice from user
    'input_choice',
    'input_choice_typewriter',
    # Get input from user and loop if input matches a set
    'input_loop',
    'input_loop_typewriter',
    # Get integer/float from user
    'input_number',
    'input_number_typewriter',
    # Print with a delay before/after the message
    'print_sleep',
    # Print with a delay after each line (sep='\n')
    'print_sleep_multiline',
    # Print with a typewriter effect
    'print_typewriter',
    # Variables
    'TYPEWRITER_SPEED',
    'SLEEP_CHAR_DELAY_NORMAL',
    'SLEEP_CHAR_DELAY_SPECIFICS'
]

TYPEWRITER_SPEED = 1
SLEEP_CHAR_DELAY_NORMAL = 0.01
SLEEP_CHAR_DELAY_SPECIFICS = {
    '.': 0.2,
    ',': 0.3,
    ';': 0.4,
    ':': 0.5,
    '?': 0.6,
    '!': 0.6
}


# ===== Generic Functions =====
def divi_zero(n, m, raiseIfZero=False, failValue=0, mode=0):
    """Division function with tweakable settings.

    Args:
        n (Real): Dividend
        m (Real): Divisor
        raiseIfZero (bool):
            If True, raise ZeroDivisionError if the denominator is 0.
        failValue (Real):
            Value to return if n == 0 or m == 0 and raiseIfZero.
        mode (Literal[-1, 0, 1]):
            0 for normal division
            -1 for floor division
            1 for ceil division

    """
    if n == 0:
        return failValue
    if m == 0:
        if raiseIfZero:
            raise ZeroDivisionError('division by zero') \
                  from ValueError('raiseIfZero flag is True')
        return failValue

    if mode == 0:
        return n / m
    elif mode == -1:
        return n // m
    elif mode == 1:
        return (n + m - 1) // m
    else:
        raise ValueError(f'Invalid mode parameter ({mode})')


# ===== Input/Print Functions =====
def input_methodize(
        prompt, apply_methods=(),
        print_func=functools.partial(print, end='')):
    """Apply given methods into input()."""
    print_func(prompt)
    input_ = input()

    for method in apply_methods:
        input_ = method(input_)

    return input_


def input_loop(
        prompt, loopIfEquals=(''),
        loopPrompt=None, loopBreak=('exit',),
        apply_methods=(str.strip, str.casefold),
        print_func=None):
    """Get input from the user, looping if it matches a set.

    Args:
        prompt (str): The first prompt to show.
        loopIfEquals (Union[Dictionary[str, str], Iterable[str]]):
            A set of potential inputs that loops the input.
            dict:
                Selects a new prompt based on the input.
                It is best used with `str.strip` and `str.casefold` passed
                into `apply_methods`.
        loopPrompt (Union[None, str]):
            None: Reuse the first prompt.
            str: Use the given string as the new prompt.
            If a dictionary is supplied to `loopIfEquals`, this
            parameter is obsolete.
        loopBreak (Optional[Iterable[str]]):
            A set of inputs that breaks out of the loop, returning
            a ValueError (but not raising it) that contains the given input.
        apply_methods: An optional iterable of methods.
            These methods will be executed on the immediate
            result of input before being validated.
        print_func (Optional[Function]):
            The function used for printing before input.
            This is helpful for passing partial versions
            of a custom print function.
            If None, uses the default print function of `input_methodize`.

    Returns:
        str: The user input.
        ValueError:
            The user input that matched `loopBreak` and broke the loop.

    """
    def input_methodize_partial(prompt):
        if print_func is None:
            return input_methodize(
                prompt, apply_methods)
        return input_methodize(
            prompt, apply_methods, print_func)

    if loopPrompt is None:
        loopPrompt = prompt

    input_ = input_methodize_partial(prompt)

    while input_ not in loopBreak:
        if input_ in loopIfEquals:
            # Get custom prompt if dictionary
            if isinstance(loopIfEquals, dict):
                new_prompt = loopIfEquals[input_]
            else:
                new_prompt = loopPrompt

            input_ = input_methodize_partial(new_prompt)
            continue

        return input_

    return ValueError(input_)


def input_loop_typewriter(
        prompt, loopIfEquals=(''),
        loopPrompt=None, loopBreak=('exit',),
        apply_methods=(str.strip, str.casefold),
        args=(), **kwargs):
    """A modified version of `input_loop` to use the typewriter effect.

    Any extra keyword arguments are passed into `print_typewriter`,
    but for positional arguments, you must pass an iterable
    directly to `args`. This is to improve legibility by separating
    positional arguments from the `input_loop` function.
    Note: You usually won't need to pass in anything for `args`
        as that should only affect the prompt messages.

    `end` is set to '' by default but can be overwritten.

    """
    kwargs.setdefault('end', '')
    # `functools.partial` is used to fill in arguments
    print_func = functools.partial(
        print_typewriter,
        *args,
        **kwargs
    )
    return input_loop(
        prompt, loopIfEquals,
        loopPrompt, loopBreak,
        apply_methods,
        print_func=print_func
    )


def input_choice(
        prompt, choices, max_answers=None, reprompt=None,
        apply_methods=(str.strip, str.casefold),
        print_func=None):
    """Get a choice from the user.

    Args:
        prompt (str): The prompt to use.
        choices (Iterable[str]): An iterable of allowed inputs.
        max_answers (Optional[int]):
            The amount of answers the user can give before returning None.
            If None, an indefinite amount of answers are allowed.
        reprompt (Union[None, str, Dictionary[str, str]]):
            Reprompt the user when an invalid input is given, or disable it.
            None: Reuse the prompt string.
            str: Use the given string as the new prompt.
            dict: Select a prompt based on the input.
                If the input is not in the dict, use reprompt['\n'].
                It is best used with `str.strip` and `str.casefold` passed
                into `apply_methods` to allow more lenient user-input.
        apply_methods: An optional iterable of methods.
            These methods will be executed on the immediate
            result of input before being validated.
        print_func (Optional[Function]):
            The function used for printing before input.
            This is helpful for passing partial versions
            of a custom print function.
            If None, uses the default print function of `input_methodize`.

    Returns:
        str: The user input matching one of the choices.
        None: Given when user types in a total of `max_answers`.

    """
    def input_methodize_partial(prompt):
        if print_func is None:
            return input_methodize(
                prompt, apply_methods)
        return input_methodize(
            prompt, apply_methods, print_func)

    if reprompt is None:
        # Reuse prompt message
        reprompt = prompt

    input_ = input_methodize_partial(prompt)

    while input_ not in choices:
        if isinstance(max_answers, int):
            max_answers -= 1
            if max_answers <= 0:
                return None
        # Get custom prompt if dictionary
        if isinstance(reprompt, dict):
            new_prompt = reprompt.get(input_, reprompt['\n'])
        else:
            new_prompt = reprompt

        input_ = input_methodize_partial(new_prompt)

    return input_


def input_choice_typewriter(
        prompt, choices, max_answers=None, reprompt=None,
        apply_methods=(str.strip, str.casefold),
        args=(), **kwargs):
    """A modified version of `input_choice` to use the typewriter effect.

    Any extra keyword arguments are passed into `print_typewriter`,
    but for positional arguments, you must pass an iterable
    directly to `args`. This is to improve legibility by separating
    positional arguments from the `input_choice` function.
    Note: You usually won't need to pass in anything for `args`
        as that should only affect the prompt messages.

    `end` is set to '' by default but can be overwritten.

    """
    kwargs.setdefault('end', '')
    # `functools.partial` is used to fill in arguments
    print_func = functools.partial(
        print_typewriter,
        *args,
        **kwargs
    )
    return input_choice(
        prompt, choices, max_answers, reprompt,
        apply_methods,
        print_func=print_func
    )


def input_number(
        prompt, invalid_prompt=None,
        low_bound=None, high_bound=None,
        low_bound_prompt=None, high_bound_prompt=None,
        integer_only=False, integer_only_prompt=None,
        max_answers=None,
        apply_methods=(str.strip,),
        print_func=None):
    """Get a number from the user.

    Args:
        prompt (str): The prompt to use.
        invalid_prompt (Optional[str]):
            The prompt to show when the input could not be converted
            into a number.
        low_bound (Optional[int]):
            The minimum number (inclusive) that can be inputted.
        high_bound (Optional[int]):
            The maximum number (inclusive) that can be inputted.
        low_bound_prompt (Optional[str]):
            The prompt to show when a number under bounds is inputted.
            If not given, will fall back to `invalid_prompt`.
        high_bound_prompt (Optional[str]):
            The prompt to show when a number over bounds is inputted.
            If not given, will fall back to `invalid_prompt`.
        integer_only (bool):
            If True, disallow decimal input.
        integer_only_prompt (Optional[str]):
            The prompt to show when a non-integer input is given.
            If not given, will fall back to `invalid_prompt`.
        max_answers (Optional[int]):
            The amount of answers the user can give
            before returning None.
            If None, an indefinite amount of answers are allowed.
        apply_methods: An optional iterable of methods.
            These methods will be executed on the immediate
            result of input before being validated.
        print_func (Optional[Function]):
            The function used for printing before input.
            This is helpful for passing partial versions
            of a custom print function.
            If None, uses the default print function of `input_methodize`.

    Returns:
        int: The user-given integer.
        float: The user-given float.
            If `integer_only` is False,
            will convert integer inputs into floats.
        None: Indicates invalid input when more than `max_answers`
            are given.

    """
    def input_methodize_partial(prompt):
        if print_func is None:
            return input_methodize(
                prompt, apply_methods)
        return input_methodize(
            prompt, apply_methods, print_func)

    def get_num(prompt):
        n = input_methodize_partial(prompt)
        try:
            return int(n) if float(n).is_integer() else float(n)
        except ValueError:
            return n

    def validate(n):
        if isinstance(n, str):
            # Failed to convert into number
            return False
        if isinstance(n, float) and integer_only:
            # Floats disallowed
            return False
        if low_bound is not None and n < low_bound:
            # Under bounds
            return False
        if high_bound is not None and n > high_bound:
            # Over bounds
            return False
        # Valid input
        return True

    def get_new_prompt(n):
        if isinstance(n, str):
            if invalid_prompt is not None:
                return invalid_prompt
            return prompt
        if isinstance(n, float) and integer_only:
            if integer_only_prompt is not None:
                return integer_only_prompt
            elif invalid_prompt is not None:
                return invalid_prompt
            return prompt
        if low_bound is not None and n < low_bound:
            if low_bound_prompt is not None:
                return low_bound_prompt
            elif invalid_prompt is not None:
                return invalid_prompt
            return prompt
        if high_bound is not None and n > high_bound:
            if high_bound_prompt is not None:
                return high_bound_prompt
            elif invalid_prompt is not None:
                return invalid_prompt
            return prompt

    input_ = get_num(prompt)

    while not validate(input_):
        if isinstance(max_answers, int):
            max_answers -= 1
            if max_answers <= 0:
                return None

        input_ = get_num(get_new_prompt(input_))

    return input_


def input_number_typewriter(
        prompt, invalid_prompt=None,
        low_bound=None, high_bound=None,
        low_bound_prompt=None, high_bound_prompt=None,
        integer_only=False, integer_only_prompt=None,
        max_answers=None,
        apply_methods=(str.strip,),
        args=(), **kwargs):
    """A modified version of `input_number` to use the typewriter effect.

    Any extra keyword arguments are passed into `print_typewriter`,
    but for positional arguments, you must pass an iterable
    directly to `args`. This is to improve legibility by separating
    positional arguments from the `input_choice` function.
    Note: You usually won't need to pass in anything for `args`
        as that should only affect the prompt messages.

    `end` is set to '' by default but can be overwritten.

    """
    kwargs.setdefault('end', '')
    # `functools.partial` is used to fill in arguments
    print_func = functools.partial(
        print_typewriter,
        *args,
        **kwargs
    )
    return input_number(
        prompt, invalid_prompt,
        low_bound, high_bound,
        low_bound_prompt, high_bound_prompt,
        integer_only, integer_only_prompt,
        max_answers,
        apply_methods,
        print_func=print_func
    )


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
        time.sleep(sleep / TYPEWRITER_SPEED)
    print(*value, **kwargs)
    if sleep_after:
        time.sleep(sleep / TYPEWRITER_SPEED)


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


def print_typewriter(
        value, *args, sep='\n', end='\n',
        sleep_char=0, sleep_char_specifics=(),
        sleep_line=0, sleep_line_after=True):
    """Print a string in typewriter fashion.

    `sep` default has been changed to '\n', allowing comma separated lines.

    Args:
        sleep_char (Real):
            The delay between each character printed, excluding newlines.
        sleep_char_specifics (Optional[Dict[str, float]]):
            A dictionary of characters that have specific sleep times.
            This is typically used for punctuation delays.
        sleep_line (Real):
            The delay between each line.
        sleep_line_after (bool):
            If True, sleep after each line instead of before.

    """
    sleep_char /= TYPEWRITER_SPEED
    sleep_line /= TYPEWRITER_SPEED
    values = sep.join([value] + [str(a) for a in args]).split('\n')

    for line in values:
        if not sleep_line_after:
            time.sleep(sleep_line)

        # Print each character
        last_sleep = 0  # Used to compensate for sleep_line_after
        for char in line:
            # Also forcibly flush the stream to print instantly,
            # otherwise the output will be buffered (noticable in terminal)
            print(char, end='', flush=True)
            if char in sleep_char_specifics:
                last_sleep = sleep_char_specifics[char] / TYPEWRITER_SPEED
                time.sleep(last_sleep)
            else:
                last_sleep = sleep_char
                time.sleep(last_sleep)

        if sleep_line_after:
            # Compensate for the sleep in the last character printed
            x = sleep_line - last_sleep
            if x > 0:
                time.sleep(x)

        # If the values only has one line, no newlines were given
        # and therefore should not print a newline
        if len(values) > 1:
            print(end='\n')

    print(end=end)


def main():
    print_typewriter(
        'Greetings software developer! My name is Cave Johnson, '
            'CEO of Aperture Science!',
        '',
        'I need you, yes you my friend, to make a, '
            'uh, "small" program for me.',
        sleep_char=SLEEP_CHAR_DELAY_NORMAL,
        sleep_char_specifics=SLEEP_CHAR_DELAY_SPECIFICS,
        sleep_line=0.5
    )
    # Get name and Title Case it
    player_name = input_loop_typewriter(
        "Now my friend, what's your name? ",
        loopIfEquals={
            '': "What's that, I didn't hear you: ",
            'cave johnson': 'Yeah, no, tell me your actual name: '
        },
        loopBreak=(),
        sleep_char=SLEEP_CHAR_DELAY_NORMAL,
        sleep_char_specifics={',': 0.3}
    ).title()

    print_typewriter(
        f'Hello {player_name}, I need a program that will help me '
            'send automated voice lines to my employees.',
        '',
        'Not that I fire anyone on the daily, but on that note, '
        'I need three things from you:',
        sleep_char=SLEEP_CHAR_DELAY_NORMAL,
        sleep_char_specifics=SLEEP_CHAR_DELAY_SPECIFICS,
        sleep_line=1
    )
    # Include dash in SLEEP_CHAR_DELAY_SPECIFICS if not there
    SLEEP_CHAR_DELAY_SPECIFICS_dash = SLEEP_CHAR_DELAY_SPECIFICS.copy()
    SLEEP_CHAR_DELAY_SPECIFICS_dash.setdefault('-', 0.5)
    print_typewriter(
        "Number 1. Your code must be written in Python. If it isn't, "
            "I'm going to be very disappointed and your contract "
            "will be terminated - don't ask me why;",
        '',
        'Number 2. I require all of my voicelines to be used, '
            'and if there are any changes to these lines, note that I '
            'will not hesitate to deport you from this world;',
        '',
        "And Number 3. Don't be late. Last time someone was late, "
            'they had a very uh, "pleasant", surprise.',
        '',
        'Now off you go, I will send you what I require '
            'along with the mentioned voice lines in an email, '
            'now I have some firing to do, Cave Johnson out!',
        sleep_char=SLEEP_CHAR_DELAY_NORMAL,
        sleep_char_specifics=SLEEP_CHAR_DELAY_SPECIFICS_dash,
        sleep_line=1
    )


if __name__ == '__main__':
    main()
