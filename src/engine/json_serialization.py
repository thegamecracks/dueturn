import collections.abc


class JSONSerializableBasic:

    @classmethod
    def from_JSON(cls, literal):
        return cls(**literal)

    def to_JSON(self):
        # Store object type so the decoder knows what object this is
        literal = {'__type__': self.__class__.__name__}

        # Store all attributes of object
        literal.update(self.__dict__)

        return literal


class JSONSerializableValues(JSONSerializableBasic):
    """Allows objects that only have the `values` attribute to be
    de/serialized to JSON."""

    def to_JSON(self):

        def to_JSON_dict(obj):
            obj_JSON = {}

            # Check for literals and sequences inside the dict
            for k, v in obj.items():
                obj_JSON[k] = to_JSON_recursive(v)
            
            return obj_JSON

        def to_JSON_recursive(obj):
            if isinstance(obj, dict):
                # Found literal; recurse into it and replace the key
                # with the deserialized version of the literal
                return to_JSON_dict(obj)
            elif hasattr(obj, 'to_JSON'):
                return obj.to_JSON()
            elif (
                    isinstance(obj, collections.abc.Sequence)
                    and not isinstance(obj, str)):
                # Found sequence; recurse for each item inside
                return [to_JSON_recursive(item) for item in obj]
            return obj

        literal = {'__type__': self.__class__.__name__}

        literal['values'] = to_JSON_dict(self.values)

        return literal
