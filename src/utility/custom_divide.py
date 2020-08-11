def custom_divide(n, m, *, raiseIfZero=False, failValue=0, mode=0):
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
