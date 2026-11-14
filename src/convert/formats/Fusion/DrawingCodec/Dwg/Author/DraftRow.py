from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import (
    DraftLink,
    DraftRecord,
)


@MakeDataClass(frozen=True, slots=True)
class DraftEed:
    AppLink: DraftLink
    EedItems: DraftRecord


@MakeDataClass(frozen=True, slots=True)
class DraftRow:
    KeyText: str
    ClassName: str
    CommonData: DraftRecord
    ClassData: DraftRecord
    EedBlocks: tuple[DraftEed, ...]
    SpareCommon: frozenset[str] = frozenset()
    SpareClass: frozenset[str] = frozenset()
