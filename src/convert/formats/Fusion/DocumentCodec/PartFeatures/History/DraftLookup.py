from collections.abc import Callable
from typing import TypeAlias

# the draft find shape must stay shared so parametric feature reconstruction uses one contract for compatible values
KDraftFind: TypeAlias = Callable[[tuple[object, ...]], int]


# the draft lookup contract needs a dedicated boundary so feature parameters remain connected to the resulting geometry
class DraftLookup:

    # draft lookup needs explicit initial state so feature parameters remain connected to the resulting geometry
    def __init__(self, Indices: dict[tuple[object, ...], int] | None) -> None:
        super().__init__()
        self.Indices = Indices

    # draft lookup needs an explicit validity boundary so feature parameters remain connected to the resulting geometry
    def __call__(self, KeyValue: tuple[object, ...]) -> int:
        if self.Indices is None:
            return 0
        if KeyValue not in self.Indices:
            raise ValueError("Fusion part journal draft references an unknown node")
        return self.Indices[KeyValue]
