from collections.abc import Callable
from typing import TypeAlias

KDraftFind: TypeAlias = Callable[[tuple[object, ...]], int]


class DraftLookup:
    def __init__(self, Indices: dict[tuple[object, ...], int] | None) -> None:
        super().__init__()
        self.Indices = Indices

    def __call__(self, KeyValue: tuple[object, ...]) -> int:
        if self.Indices is None:
            return 0
        if KeyValue not in self.Indices:
            raise ValueError("Fusion part journal draft references an unknown node")
        return self.Indices[KeyValue]
