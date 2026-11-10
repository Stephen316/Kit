# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from interchange.geometry.models.Sketch import SketchEntity

# exact tuples distinguish separate selected portions of one native primitive
KTrimSelector = tuple[int, int, int, int, int, int, int]

# source tags are resolved before geometry interprets their stored portion selectors
KTrimMember = tuple[SketchEntity, KTrimSelector]


# one bounded outer loop retains native membership without inventing traversal
def ReadTrimMembers(
    BodyValue: bytes, DescriptorId: int, Sources: dict[int, SketchEntity]
) -> tuple[KTrimMember, ...]:
    Cursor = MetaCursor(BodyValue)
    if (
        Cursor.TakeBytes(2) != bytes(2)
        or ReadNativeRef(Cursor) != DescriptorId
        or Cursor.ReadWord() != 1
        or Cursor.ReadWord() != 1
    ):
        raise ValueError("Fusion trimmed profile requires one owned outer loop")
    Count = Cursor.ReadCount(4)
    if Count < 2:
        raise ValueError("Fusion trimmed profile needs two to four selected portions")
    Members: list[KTrimMember] = []
    SeenValues: set[KTrimSelector] = set()
    for _ in range(Count):
        CodeValue = Cursor.ReadWord()
        TagValue = Cursor.ReadLong()
        Secondary = Cursor.ReadLong()
        Direction = Cursor.ReadWord()
        Ordinal = Cursor.ReadWord()
        Parts = Cursor.ReadWord()
        Opaque = Cursor.ReadLong()
        Selector = (CodeValue, TagValue, Secondary, Direction, Ordinal, Parts, Opaque)
        Entity = Sources.get(TagValue)
        if (
            CodeValue != 3
            or Secondary != 0
            or Opaque != 0
            or Direction not in (0, 1)
            or Entity is None
            or Selector in SeenValues
        ):
            raise ValueError("Unsupported or ambiguous Fusion trimmed profile selector")
        SeenValues.add(Selector)
        Members.append((Entity, Selector))
    if Cursor.TakeBytes(5) != b"\1\0\0\0\0" or Cursor.Offset != len(BodyValue):
        raise ValueError("Unsupported Fusion trimmed outer loop extent")
    return tuple(Members)
