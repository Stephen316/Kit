# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from interchange.geometry.models.Sketch import SketchEntity

# exact tuples distinguish separate selected portions of one native primitive
TrimSelector = tuple[int, int, int, int, int, int, int]

# source tags are resolved before geometry interprets their stored portion selectors
TrimMember = tuple[SketchEntity, TrimSelector]


# one bounded outer loop retains native membership without inventing traversal
def ReadTrimMembers(
    BodyValue: bytes, DescriptorId: int, Sources: dict[int, SketchEntity]
) -> tuple[TrimMember, ...]:
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
    Members: list[TrimMember] = []
    Seen: set[TrimSelector] = set()
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
            or Selector in Seen
        ):
            raise ValueError("Unsupported or ambiguous Fusion trimmed profile selector")
        Seen.add(Selector)
        Members.append((Entity, Selector))
    if Cursor.TakeBytes(5) != b"\1\0\0\0\0" or Cursor.Offset != len(BodyValue):
        raise ValueError("Unsupported Fusion trimmed outer loop extent")
    return tuple(Members)
