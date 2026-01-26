"""Utility types for building shell arguments."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Optional

class ArgList(list):
    def __init__(self, *values: Any):
        super().__init__(self._flatten(values))

    @staticmethod
    def _flatten(values: tuple[Any, ...]) -> Iterable[Any]:
        if len(values) == 1 and isinstance(values[0], Iterable) and not isinstance(values[0], (str, bytes)):
            return values[0]
        return values

    def concat(self, separator: Optional[str] = None) -> str:
        sep = " " if separator is None else str(separator)
        return sep.join(self._stringify())

    def extend(self, values: Any) -> None:
        super().extend(self._flatten((values,)))

    def __add__(self, other: Any):
        result = self.__class__(self)
        result.extend(other)
        return result

    def __radd__(self, other: Any):
        result = self.__class__(other)
        result.extend(self)
        return result

    def __iadd__(self, other: Any):
        self.extend(other)
        return self

    def _stringify(self) -> list[str]:
        return [str(item) for item in self]

    def __str__(self) -> str:
        return self.concat()

    def __repr__(self) -> str:
        return f"[{self.concat(',')}]"
