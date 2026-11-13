from __future__ import annotations

from types import ModuleType
from typing import Protocol


class ForwardCall(Protocol):
    def __call__(self, *ArgList: object, **KeyArgs: object) -> ModuleType:
        raise TypeError("forwarded import callables require a concrete implementation")
