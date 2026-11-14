from dataclasses import dataclass as MakeDataClass
from dataclasses import field as MakeField

from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftRow import DraftRow
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import KDraftValue


def EmptyRows() -> list[DraftRow]:
    return []


def EmptySlots() -> dict[str, list[KDraftValue]]:
    return {}


@MakeDataClass(slots=True)
class DraftBook:
    FixedHandles: dict[str, int]
    DraftRows: list[DraftRow] = MakeField(default_factory=EmptyRows)
    SlotItems: dict[str, list[KDraftValue]] = MakeField(default_factory=EmptySlots)
