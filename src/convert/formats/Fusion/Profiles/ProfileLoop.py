# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from interchange.geometry.models.Sketch import Sketch, SketchEntity
from interchange.enums.EnumGeometry import GeometryKind


# native curve tags identify complete profile members inside one selected sketch
def ReadProfileLoop(
    BodyValue: bytes, DescriptorId: int, SketchValue: Sketch
) -> tuple[tuple[SketchEntity, ...], tuple[int, ...]]:
    Cursor = MetaCursor(BodyValue)
    if Cursor.TakeBytes(2) != bytes(2) or ReadNativeRef(Cursor) != DescriptorId:
        raise ValueError("Fusion profile loop owner disagrees")
    if Cursor.ReadWord() != 1 or Cursor.ReadWord() != 1:
        raise ValueError("Fusion profile requires one whole outer loop")
    Count = Cursor.ReadCount(64)
    if Count == 0:
        raise ValueError("Fusion profile loop has no curves")
    Curves: dict[int, list[SketchEntity]] = {}
    for Entity in SketchValue.entities:
        TagValue = Entity.attributes.get("fusion.entity_tag")
        if Entity.kind != GeometryKind.KPoint and isinstance(TagValue, int):
            Curves.setdefault(TagValue, []).append(Entity)
    Members: list[SketchEntity] = []
    Directions: list[int] = []
    for _ in range(Count):
        CodeValue, TagValue, Secondary = (
            Cursor.ReadWord(),
            Cursor.ReadLong(),
            Cursor.ReadLong(),
        )
        Direction, FirstFlag, SecondFlag = (Cursor.ReadWord() for _ in range(3))
        Opaque = Cursor.ReadLong()
        if (
            CodeValue != 3
            or Secondary != 0
            or Direction not in (0, 1)
            or (FirstFlag, SecondFlag) != (1, 1)
            or Opaque != 0
        ):
            raise ValueError("Unsupported Fusion trimmed profile reference")
        Matches = Curves.get(TagValue, [])
        if len(Matches) != 1 or Matches[0].construction:
            raise ValueError(
                "Fusion profile curve is unavailable, ambiguous, or construction"
            )
        Members.append(Matches[0])
        Directions.append(Direction)
    if (
        Cursor.TakeBytes(5) != b"\1\0\0\0\0"
        or Cursor.Offset != len(BodyValue)
        or len({Entity.id for Entity in Members}) != Count
    ):
        raise ValueError("Invalid Fusion outer profile framing")
    return tuple(Members), tuple(Directions)
