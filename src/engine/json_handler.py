"""This module provides a function for deserializing JSON with custom objects
inside of the literals.

Whenever a custom object is serialized into JSON, the object should provide a
__type__ key containing the name of the class. This name is used to determine
what object should be used to deserialize the literal.

When the literal contains more literals inside, `object_hook` will recursively
deserialize those literals.

Whenever a JSON object needs to be loaded containing custom objects,
pass `object_hook` into the `object_hook` parameter.

See `objects` variable for what objects are recognized.

When a list of moves or other custom objects need to be saved,
use `json_dump_sequence`:
    >>> json_dump_sequence(moveList, './data/moves.json', indent=4)
"""
import json

# Import objects that are expected to be deserialized
from .bound import Bound
from .item import Item
from .move import Move
from .movetype import MoveType
from .skill import Skill
from .status_effect import StatusEffect

objects = {
    'Bound': Bound,
    'Item': Item,
    'Move': Move,
    'MoveType': MoveType,
    'Skill': Skill,
    'StatusEffect': StatusEffect
}


def dump_sequence(objects, path, *args, **kwargs):
    """Dump a sequence of JSON-serializable objects into a file."""
    objects_json = [
        item.to_JSON() if hasattr(item, 'to_JSON')
        else item
        for item in objects
    ]

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(objects_json, f, *args, **kwargs)


def load(path, *args, json_kwargs={}, **kwargs):
    """Opens `path` as a file and fills in object_hook argument
    with this module's `object_hook` function.

    Example:
        >>> json_handler.load(
        ...     'src/engine/data/moves.json', encoding='utf-8')

    Args:
        path (str): The path of the file to open.
        *args: Positional arguments for open().
        json_kwargs: Keyword arguments for json.load().
        **kwargs: Keyword arguments for open().

    """
    with open(path, *args, **kwargs) as f:
        return json.load(f, object_hook=object_hook, **json_kwargs)


def object_hook(literal):
    """Automatically figures out what object should be used
    to deserialize the literal.

    The literal must come with a __type__ key specifying what object
    to call `from_JSON` with.

    """
    def from_JSON_literal(literal):
        type_ = literal.get('__type__')
        if type_ is not None:
            cls = objects.get(type_)
            if cls is None:
                raise TypeError(f'Unknown __type__ value {type_!r}')

            del literal['__type__']

            # Check for literals and sequences inside the literal
            for k, v in literal.items():
                literal[k] = from_JSON_recursive(v)

            return cls.from_JSON(literal)
        return literal

    def from_JSON_recursive(obj):
        if isinstance(obj, dict):
            # Found literal; recurse into it and replace the key
            # with the deserialized version of the literal
            return from_JSON_literal(obj)
        elif isinstance(obj, list):
            # Found sequence; recurse for each item inside
            return [from_JSON_recursive(item) for item in obj]
        return obj

    return from_JSON_recursive(literal)
