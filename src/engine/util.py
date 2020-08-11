import time


def num(x):
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
