from __future__ import annotations

from types import ModuleType
from typing import Protocol


# the forward call contract needs a dedicated boundary so dependency changes cannot revive stale passing results
class ForwardCall(Protocol):

    # forward call needs an explicit validity boundary so dependency changes cannot revive stale passing results
    def __call__(self, *ArgList: object, **KeyArgs: object) -> ModuleType:
        raise TypeError("forwarded import callables require a concrete implementation")
