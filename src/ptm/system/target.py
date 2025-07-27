import os
from typing import List, Callable, Any

from .logger import plog
from .utils import _get_target_name, _get_timestamp, _get_depends

class BuildTarget:
    def __init__(self, recipe: Callable, target: str, depends: List[str]):
        self.target = target
        self.depends = depends
        self.recipe = recipe
        self.timestamp = _get_timestamp(self.target)

    def _check_valid(self) -> bool:
        if self.timestamp == 0:
            return True

        for depend in self.depends:
            if _get_timestamp(depend) >= self.timestamp:
                return True

        return False

    def build(self, **kwargs) -> Any:
        if not self._check_valid():
            plog.info(f"Target '{self.target}' is up to date")

        else:
            plog.info(f"Building target: {self.target}")
            if os.path.isabs(self.target):
                os.makedirs(os.path.dirname(self.target), exist_ok=True)

            self.recipe(**kwargs)
            self.timestamp = _get_timestamp(self.target)
