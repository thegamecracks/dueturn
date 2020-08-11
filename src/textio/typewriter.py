"""Provides functions for typewriter I/O."""
import functools
import time

from . import inputting

__all__ = [
    'input_boolean_typewriter',
    'input_choice_typewriter',
    'input_loop_if_equals_typewriter',
    'input_number_typewriter',
    'print_typewriter',
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


def input_boolean_typewriter(
        prompt='', repeat_prompt=None,
        true=('yes', 'y'), false=('no', 'n'),
        show_option_count=-1,
        apply_methods=(str.strip, str.casefold),
        print_func=print,
        args=(), **kwargs):
    """A modified version of `input_loop_if_equals` to use
    the typewriter effect.

    Any extra keyword arguments are passed into `print_typewriter`,
    but for positional arguments, you must pass an iterable
    directly to `args`. This is to improve legibility by separating
    positional arguments from the `input_boolean` function.
    Note: You usually won't need to pass in anything for `args`
        as that should only affect the prompt messages.

    `end` is set to '' by default but can be overwritten.

    """
    kwargs.setdefault('end', '')
    print_func = functools.partial(
        print_typewriter,
        *args,
        **kwargs
    )
    return inputting.input_boolean(
        prompt, repeat_prompt,
        true, false,
        show_option_count,
        apply_methods,
        print_func=print_func
    )


def input_loop_if_equals_typewriter(
        prompt='', repeat_prompt=None,
        loop_if_equals=None, break_string=None,
        apply_methods=(str.strip, str.casefold),
        print_func=None,
        args=(), **kwargs):
    """A modified version of `input_loop_if_equals` to use
    the typewriter effect.

    Any extra keyword arguments are passed into `print_typewriter`,
    but for positional arguments, you must pass an iterable
    directly to `args`. This is to improve legibility by separating
    positional arguments from the `input_loop_if_equals` function.
    Note: You usually won't need to pass in anything for `args`
        as that should only affect the prompt messages.

    `end` is set to '' by default but can be overwritten.

    """
    kwargs.setdefault('end', '')
    print_func = functools.partial(
        print_typewriter,
        *args,
        **kwargs
    )
    return inputting.input_loop_if_equals(
        prompt, repeat_prompt,
        loop_if_equals, break_string,
        apply_methods,
        print_func=print_func
    )


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
    print_func = functools.partial(
        print_typewriter,
        *args,
        **kwargs
    )
    return inputting.input_choice(
        prompt, choices, max_answers, reprompt,
        apply_methods,
        print_func=print_func
    )


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
    print_func = functools.partial(
        print_typewriter,
        *args,
        **kwargs
    )
    return inputting.input_number(
        prompt, invalid_prompt,
        low_bound, high_bound,
        low_bound_prompt, high_bound_prompt,
        integer_only, integer_only_prompt,
        max_answers,
        apply_methods,
        print_func=print_func
    )


def print_typewriter(
        value, *args, sep='\n', end='\n',
        sleep_char=0, sleep_char_specifics=(),
        sleep_line=0, sleep_line_after=True):
    """Print a string in typewriter fashion.

    `sep` default has been changed to '\n', allowing comma separated lines.

    Args:
        sleep_char (Union[int, float]):
            The delay between each character printed, excluding newlines.
        sleep_char_specifics (Optional[Dict[str, float]]):
            A dictionary of characters that have specific sleep times.
            This is typically used for punctuation delays.
        sleep_line (Union[int, float]):
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
    player_name = input_loop_if_equals_typewriter(
        "Now my friend, what's your name? ",
        loop_if_equals={
            '': "What's that, I didn't hear you: ",
            'cave johnson': 'Yeah, no, tell me your actual name: '
        },
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
