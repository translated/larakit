import json


class Namespace(object):
    @classmethod
    def from_json_string(cls, json_string):
        return cls(**json.loads(json_string))

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get(self, key, default=None):
        return self.__dict__.get(key, default)

    def __getattr__(self, key):
        return self.get(key)

    def set(self, key, value):
        def parse(val):
            if isinstance(val, dict):
                return Namespace(**val)
            elif isinstance(val, list):
                return [parse(v) for v in val]
            return val

        super().__setattr__(key, parse(value))

    def __setattr__(self, key, value):
        self.set(key, value)

    def has(self, key):
        return key in self.__dict__

    def __contains__(self, key):
        return self.has(key)

    def __repr__(self):
        return 'Namespace' + str(self.__dict__)

    def __str__(self):
        return repr(self)

    def to_json(self):
        def _convert(value):
            if isinstance(value, Namespace):
                return value.to_json()
            elif isinstance(value, list):
                return [_convert(v) for v in value]
            return value

        return {key: _convert(value) for key, value in self.__dict__.items()}
