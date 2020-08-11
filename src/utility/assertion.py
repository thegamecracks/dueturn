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
