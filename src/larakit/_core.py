import json
import os
from typing import Dict, Any


class Namespace:
    @classmethod
    def from_json_string(cls, json_string: str) -> 'Namespace':
        return cls(**json.loads(json_string))

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            self.set(key, value)

    def get(self, key, default=None):
        return self.__dict__.get(key, default)

    def __getattr__(self, key):
        return self.get(key)

    def _set_private(self, key, value):
        if not key.startswith('_'):
            raise KeyError(f'Private properties must start with an underscore: {key}')
        super().__setattr__(key, value)

    def set(self, key, value):
        if key.startswith('_'):
            raise KeyError(f'Private properties are not allowed: {key}')

        def parse(val):
            if isinstance(val, dict):
                return Namespace(**val)
            if isinstance(val, list):
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
        return str(self.to_json())

    def to_json(self) -> Dict[str, Any]:
        def _to_json(value):
            if isinstance(value, Namespace):
                return value.to_json()
            if isinstance(value, list):
                return [_to_json(v) for v in value]
            return value

        return {key: _to_json(value) for key, value in self.__dict__.items() if not key.startswith('_')}


class StatefulNamespace(Namespace):
    def __init__(self, path: str, autosave: bool = False, **default_kwargs):
        super().__init__()
        self._set_private('_path', path)
        self._set_private('_autosave', autosave)

        for key, value in default_kwargs.items():
            super().set(key, value)

        if os.path.isfile(self._path):
            with open(self._path, 'r', encoding='utf-8') as f_input:
                data = json.load(f_input)
                for key, value in data.items():
                    super().set(key, value)

        if self._autosave:
            self.save()

    @property
    def path(self) -> str:
        return self._path

    @property
    def autosave(self) -> bool:
        return self._autosave

    def set(self, key, value):
        super().set(key, value)

        if self._autosave:
            self.save()

    def save(self, indent: int = 2, sort_keys: bool = True):
        with open(self._path, 'w', encoding='utf-8') as f_output:
            f_output.write(json.dumps(self.to_json(), indent=indent, sort_keys=sort_keys))
