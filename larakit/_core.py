import json
import os


class Namespace(object):
    @classmethod
    def from_json_string(cls, json_string):
        return cls(**json.loads(json_string))

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            self._internal_set(key, value)

    def _assign(self, key, value):
        def parse(val):
            if isinstance(val, dict):
                return Namespace(**val)
            elif isinstance(val, list):
                return [parse(v) for v in val]
            return val

        super().__setattr__(key, parse(value))

    def get(self, key, default=None):
        return self.__dict__.get(key, default)

    def __getattr__(self, key):
        return self.get(key)

    def set(self, key, value):
        self._assign(key, value)

    def __setattr__(self, key, value):
        self._assign(key, value)

    def has(self, key):
        return key in self.__dict__

    def __contains__(self, key):
        return self.has(key)

    def __repr__(self):
        return f'{self.__class__.__name__}{self.__dict__}'

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


class StatefulNamespace(Namespace):
    def __init__(self, path: str, autosave: bool = False, **default_kwargs):
        super().__init__(**default_kwargs)
        self.__path = path
        self.__autosave = autosave

        if os.path.isfile(self.path):
            with open(self.path, 'r', encoding='utf-8') as f_input:
                data = json.load(f_input)
                for key, value in data.items():
                    self._assign(key, value)
        else:
            for key, value in default_kwargs.items():
                self._assign(key, value)

        if self.__autosave:
            self.save()

    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        if self.__autosave:
            self.save()

    def set(self, key, value):
        super().set(key, value)
        if self.__autosave:
            self.save()

    def save(self) -> None:
        with open(self.path, 'w', encoding='utf-8') as f_output:
            f_output.write(json.dumps(self.namespace.to_json(), indent=2, sort_keys=True))
