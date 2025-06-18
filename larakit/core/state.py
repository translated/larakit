import json
import os
from typing import Any

from larakit.core.namespace import Namespace


class State:
    def __init__(self, path: str, autosave: bool = False, override: bool = False, **kwargs) -> None:
        self.path = path
        self.autosave = autosave

        if os.path.isfile(self.path):
            with open(self.path, 'r', encoding='utf-8') as f_input:
                self.namespace = Namespace(**json.load(f_input))

            if override:
                self.update(**kwargs)
        else:
            self.namespace = Namespace(**kwargs)

        if self.autosave:
            self.save()

    def update(self, key: str, value: Any) -> None:
        self.namespace.set(key, value)

        if self.autosave:
            self.save()

    def get(self, key: str, default: Any = None) -> Any:
        return self.namespace.get(key, default)

    def save(self) -> None:
        with open(self.path, 'w', encoding='utf-8') as f_output:
            f_output.write(json.dumps(self.namespace.to_json(), indent=2, sort_keys=True))
