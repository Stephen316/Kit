from dataclasses import dataclass as MakeDataClass
from typing import TypeAlias, Union

from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef

KSlotItems = 0
KSlotCount = 1
KSlotBytes = 2
KSlotFirst = 3
KHandleNumber = -1


@MakeDataClass(frozen=True, slots=True)
class DraftLink:
    RefCode: int
    KeyText: str


@MakeDataClass(frozen=True, slots=True)
class DraftSlot:
    SlotName: str
    SlotForm: int


@MakeDataClass(frozen=True, slots=True)
class DraftRecord:
    DraftFields: tuple[tuple[str, "KDraftValue"], ...]


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
