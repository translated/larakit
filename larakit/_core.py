import json
import os
from typing import Dict


class Namespace(object):
    @classmethod
    def from_json_string(cls, json_string):
        return cls(**json.loads(json_string))

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            self.set(key, value)

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
        return f'{self.__class__.__name__}{self.__dict__}'

    def __str__(self):
        return repr(self)

    @staticmethod
    def _convert(value):
        if isinstance(value, Namespace):
            return value.to_json()
        elif isinstance(value, list):
            return [Namespace._convert(v) for v in value]
        return value

    def to_json(self):
        return {key: Namespace._convert(value) for key, value in self.__dict__.items()}


class StatefulNamespace(Namespace):
    def __init__(self, path: str, autosave: bool = False, **default_kwargs):
        super().__init__(**default_kwargs)
        self.__path = path
        self.__autosave = autosave

        if os.path.isfile(self.__path):
            with open(self.__path, 'r', encoding='utf-8') as f_input:
                data = json.load(f_input)
                for key, value in data.items():
                    super().set(key, value)
        else:
            for key, value in default_kwargs.items():
                super().set(key, value)

        if self.__autosave:
            self.save()

    def __setattr__(self, key, value):
        self.set(key, value)

    def set(self, key, value):
        super().set(key, value)
        if self.__autosave:
            self.save()

    def _get_dict(self) -> Dict:
        return {key: value for key, value in self.__dict__.items() if
                not key.startswith(f'_{self.__class__.__name__}__')}

    def save(self) -> None:
        with open(self.__path, 'w', encoding='utf-8') as f_output:
            f_output.write(json.dumps(self.to_json(), indent=2, sort_keys=True))

    def to_json(self):
        return {key: Namespace._convert(value) for key, value in self._get_dict().items()}

    def __repr__(self):
        return f'{self.__class__.__name__}{self._get_dict()}'
