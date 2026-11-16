from dataclasses import dataclass as MakeDataClass
from dataclasses import field as MakeField

from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftRow import DraftRow
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import KDraftValue


# the empty rows contract needs a shared interpretation so drawing objects retain valid ownership and reference relationships
def EmptyRows() -> list[DraftRow]:
    return []


# the empty slots contract needs a shared interpretation so drawing objects retain valid ownership and reference relationships
def EmptySlots() -> dict[str, list[KDraftValue]]:
    return {}


# draft book needs an explicit state contract so drawing objects retain valid ownership and reference relationships
@MakeDataClass(slots=True)
class DraftBook:
    FixedHandles: dict[str, int]
    DraftRows: list[DraftRow] = MakeField(default_factory=EmptyRows)
    SlotItems: dict[str, list[KDraftValue]] = MakeField(default_factory=EmptySlots)
