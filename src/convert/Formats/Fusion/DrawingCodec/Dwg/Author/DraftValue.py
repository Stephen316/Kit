from dataclasses import dataclass as MakeDataClass
from typing import TypeAlias, Union

from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef

# slot items must remain consistent across callers so drawing objects retain valid ownership and reference relationships
KSlotItems = 0

# slot count needs one explicit bound so native drawing authoring cannot accept inconsistent resource or layout limits
KSlotCount = 1

# slot bytes must remain consistent across callers so drawing objects retain valid ownership and reference relationships
KSlotBytes = 2

# slot first must remain consistent across callers so drawing objects retain valid ownership and reference relationships
KSlotFirst = 3

# handle number must remain consistent across callers so drawing objects retain valid ownership and reference relationships
KHandleNumber = -1


# draft link needs an explicit state contract so drawing objects retain valid ownership and reference relationships
@MakeDataClass(frozen=True, slots=True)
class DraftLink:
    RefCode: int
    KeyText: str


# draft slot needs an explicit state contract so drawing objects retain valid ownership and reference relationships
@MakeDataClass(frozen=True, slots=True)
class DraftSlot:
    SlotName: str
    SlotForm: int


# draft record needs an explicit state contract so drawing objects retain valid ownership and reference relationships
@MakeDataClass(frozen=True, slots=True)
class DraftRecord:
    DraftFields: tuple[tuple[str, "KDraftValue"], ...]


# the draft value shape must stay shared so native drawing authoring uses one contract for compatible values
KDraftValue: TypeAlias = Union[
    int,
    float,
    str,
    bytes,
    DwgHandleRef,
    DraftLink,
    DraftSlot,
    DraftRecord,
    tuple["KDraftValue", ...],
]
