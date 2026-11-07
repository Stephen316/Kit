# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from struct import pack as Pack

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
def TestProfileOrder() -> None:
    Lines = MakeLines(((0.0, 0.0), (2.0, 0.0), (2.0, 1.0), (0.0, 1.0)))
    Source = Sketch(
        id="sketch", name="rectangle", support_plane_id="plane", entities=Lines
    )
    BodyValue = (
        bytes(2)
        + NativeRef(99)
        + Pack("<III", 1, 1, 4)
        + b"".join(
            Pack("<IQQIIIQ", 3, TagValue, 0, 0, 1, 1, 0) for TagValue in (1, 3, 2, 4)
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
        ReadProfileLoop(BodyValue, 100, Source)


# connectivity alone must not approve a crossed ring or an open selection
def TestRejectRing() -> None:
    Crossed = MakeLines(((0.0, 0.0), (2.0, 1.0), (0.0, 1.0), (2.0, 0.0)))
    with Raises(ValueError, match="crossed or nonconvex"):
        OrderLineRing(Crossed)
    Rectangle = MakeLines(((0.0, 0.0), (2.0, 0.0), (2.0, 1.0), (0.0, 1.0)))
    with Raises(ValueError, match="does not close"):
        OrderLineRing(Rectangle[:3])
