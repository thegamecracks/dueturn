from . import util
from .colorio import format_color

__all__ = [
    'input_boolean',
    'input_choice',
    'input_loop_if_equals',
    'input_number'
]


def input_boolean(
        prompt, repeat_prompt=None,
        true=('yes', 'y'), false=('no', 'n'),
        show_option_count=-1,
        apply_methods=(str.strip, str.casefold),
        print_func=None):
    """Prompt the user for a boolean answer.

    When prompting, input is lowered and stripped regardless of `input_func`.

    Example:
        >>> input_boolean(
        ...     prompt='Type {true} to confirm:',
        ...     repeat_prompt='Unknown answer: ',
        ...     true=('yes','y'),
        ...     false=('no', 'n'),
        ...     show_option_count=2
        ... )
        Type (yes/y) to confirm:

    Args:
        prompt (str): The message to prompt.
        repeat_prompt (str): The message to prompt when the user gives
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
        apply_methods: An optional iterable of methods.
            These methods will be executed on the immediate
            result of input before being validated.
        print_func: The function to use to display prompts.
            Defaults to print().

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
        prompt = format_color(
            prompt,
            namespace={'true': true_str, 'false': false_str}
        )
        if repeat_prompt is None:
            repeat_prompt = prompt
        else:
            repeat_prompt = format_color(
                repeat_prompt,
                namespace={'true': true_str, 'false': false_str}
            )
    else:
        prompt = format_color(prompt)
        if repeat_prompt is None:
            repeat_prompt = prompt
        else:
            repeat_prompt = format_color(repeat_prompt)

    # Get input
    ans = util.input_methodize(prompt, apply_methods, print_func)

    while (meaning := parse(ans)) is None:
        ans = util.input_methodize(repeat_prompt, apply_methods, print_func)

    return meaning


def input_choice(
        prompt, choices, max_answers=None, repeat_prompt=None,
        apply_methods=(str.strip, str.casefold),
        print_func=None):
    """Get a choice from the user.

    Args:
        prompt (str): The prompt to use.
        choices (Iterable[str]): An iterable of allowed inputs.
        max_answers (Optional[int]):
            The amount of answers the user can give before returning None.
            If None, an indefinite amount of answers are allowed.
        repeat_prompt (Union[None, str, Dictionary[str, str]]):
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
    if repeat_prompt is None:
        # Reuse prompt message
        repeat_prompt = prompt

    input_ = util.input_methodize(prompt, apply_methods, print_func)

    while input_ not in choices:
        if isinstance(max_answers, int):
            max_answers -= 1
            if max_answers <= 0:
                return None
        # Get custom prompt if dictionary
        if isinstance(repeat_prompt, dict):
            new_prompt = repeat_prompt.get(input_, repeat_prompt['\n'])
        else:
            new_prompt = repeat_prompt

        input_ = util.input_methodize(new_prompt, apply_methods, print_func)

    return input_


def input_loop_if_equals(
        prompt='', repeat_prompt=None,
        loop_if_equals=None, break_string=None,
        apply_methods=(str.strip, str.casefold),
        print_func=None):
    """Prompt the user for a string and loop if it matches a set of strings.

    Example:
        >>> input_loop_if_equals(
        ...     prompt='Type your name:',
        ...     repeat_prompt='That name is already taken! ',
        ...     loop_if_equals=('foo', 'bar'),
        ...     break_string='exit'
        ... )
        Type your name:

    Args:
        prompt (str): The message to prompt.
        repeat_prompt (str): The message to prompt when the user
            provides an answer matching `loop_if_equals`.
            Leave as None to re-use `prompt`.
        loop_if_equals (Optional[Set[str]]): If provided,
            loops the prompt using `repeat_message` when the user
            types an answer in `loop_if_equals`.
        break_string (Optional[str]): If provided, returns None
            when the user types an answer equal to this.
        apply_methods: An optional iterable of methods.
            These methods will be executed on the immediate
            result of input before being validated.
        print_func (Optional[Function]):
            The function used for printing before input.
            This is helpful for passing partial versions
            of a custom print function.
            If None, uses the default print function of `input_methodize`.

    Returns:
        str: The user input not matching `loop_if_equals` or `break_string`.
        None: Given when user types in a total of `max_answers`.

    """
    def parse(ans):
        if ans == break_string:
            return None
        elif ans in loop_if_equals:
            return True
        return ans

    if repeat_prompt is None:
        repeat_prompt = prompt

    ans = util.input_methodize(prompt, apply_methods, print_func)

    while parse(ans) is True:
        ans = util.input_methodize(repeat_prompt, apply_methods, print_func)

    return ans


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
    def get_num(prompt):
        n = util.input_methodize(prompt, apply_methods, print_func)
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
