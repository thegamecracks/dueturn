import functools

print_without_newline = functools.partial(print, end='')


def input_methodize(
        prompt, apply_methods=(),
        print_func=None):
    """Apply given methods into input()."""
    if print_func is None:
        print_func = print_without_newline

    print_func(prompt)
    input_ = input()

    for method in apply_methods:
        input_ = method(input_)

    return input_
