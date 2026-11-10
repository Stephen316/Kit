# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from struct import pack as PackData

from pytest import raises as Raises

from convert.formats.Fusion.Profiles.LineRing import OrderLineRing
from convert.formats.Fusion.Profiles.ProfileLoop import ReadProfileLoop
from interchange.core.Common import FreezeMapping
from interchange.enums.EnumGeometry import GeometryKind
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Sketch import Sketch, SketchEntity
from interchange.geometry.models.VectorPlane import PlaneVector
from tests.convert.formats.FusionHistoryTests import NativeRef


# the fixture supplies finite lines and independent native tags for membership lookup
def MakeLines(Points: tuple[tuple[float, float], ...]) -> tuple[SketchEntity, ...]:
    return tuple(
        SketchEntity(
            id=f"line-{Index}",
            kind=GeometryKind.KLine,
            geometry=LineGeometry(
                PlaneVector(*Start), PlaneVector(*Points[(Index + 1) % len(Points)])
            ),
            attributes=FreezeMapping({"fusion.entity_tag": Index + 1}),
        )
        for Index, Start in enumerate(Points)
    )


# whole native members must preserve source order separately from geometric traversal
def TestRingOrder() -> None:
    Lines = MakeLines(((0.0, 0.0), (2.0, 0.0), (2.0, 1.0), (0.0, 1.0)))
    Source = Sketch(
        id="sketch", name="rectangle", support_plane_id="plane", entities=Lines
    )
    BodyValue = (
        bytes(2)
        + NativeRef(99)
        + PackData("<III", 1, 1, 4)
        + b"".join(
            PackData("<IQQIIIQ", 3, TagValue, 0, 0, 1, 1, 0)
            for TagValue in (1, 3, 2, 4)
        )
        + b"\1"
        + bytes(4)
    )
    Members, Directions = ReadProfileLoop(BodyValue, 99, Source)
    assert tuple(Entity.id for Entity in Members) == (
        "line-0",
        "line-2",
        "line-1",
        "line-3",
    )
    assert Directions == (0, 0, 0, 0)
    assert OrderLineRing(Members) == ("line-0", "line-1", "line-2", "line-3")
    with Raises(ValueError, match="owner disagrees"):
        _ = ReadProfileLoop(BodyValue, 100, Source)


# connectivity alone must not approve a crossed ring or an open selection
def TestRejectRing() -> None:
    Crossed = MakeLines(((0.0, 0.0), (2.0, 1.0), (0.0, 1.0), (2.0, 0.0)))
    with Raises(ValueError, match="crossed or nonconvex"):
        _ = OrderLineRing(Crossed)
    Rectangle = MakeLines(((0.0, 0.0), (2.0, 0.0), (2.0, 1.0), (0.0, 1.0)))
    with Raises(ValueError, match="does not close"):
        _ = OrderLineRing(Rectangle[:3])
