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


def list_copy(sequence):
    """Recursively copy each item in a list."""
    new = []
    for v in sequence:
        if isinstance(v, list):
            new.append(list_copy(v))
        elif isinstance(v, dict):
            new.append(dict_copy(v))
        elif hasattr(v, 'copy'):
            new.append(v.copy())
        else:
            new.append(v)
    return new
