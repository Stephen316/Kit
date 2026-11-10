# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import isfinite as IsFinite

from convert.formats.Fusion.Sketches.SketchPrimitive import IsSamePoint
from interchange.geometry.models.GeometryCurves import CircleGeometry, LineGeometry
from interchange.geometry.models.Sketch import SketchEntity
from interchange.geometry.models.VectorPlane import PlaneVector


# geometric closure validates native membership without treating its order as traversal
def OrderLineRing(Members: tuple[SketchEntity, ...]) -> tuple[str, ...]:
    if len(Members) == 1 and isinstance(Members[0].geometry, CircleGeometry):
        return (Members[0].id,)
    Lines: list[tuple[str, LineGeometry]] = []
    for Entity in Members:
        if not isinstance(Entity.geometry, LineGeometry):
            raise ValueError("Fusion profile requires a circle or complete line ring")
        Lines.append((Entity.id, Entity.geometry))
    if len(Lines) < 3:
        raise ValueError("Fusion line profile requires at least three sides")
    FirstId, FirstLine = Lines.pop(0)
    Start = FirstLine.start
    Points = [Start, FirstLine.end]
    Ordered = [FirstId]
    while Lines:
        TipValue = Points[-1]
        Matches = [
            Index
            for Index, (_, LineValue) in enumerate(Lines)
            if IsSamePoint(LineValue.start, TipValue)
            or IsSamePoint(LineValue.end, TipValue)
        ]
        if len(Matches) != 1:
            raise ValueError("Fusion profile line chain is open or branches")
        EntityId, LineValue = Lines.pop(Matches[0])
        Points.append(
            LineValue.end if IsSamePoint(LineValue.start, TipValue) else LineValue.start
        )
        Ordered.append(EntityId)
    if not IsSamePoint(Points[-1], Start):
        raise ValueError("Fusion profile does not close")
    CheckConvex(tuple(Points[:-1]))
    return tuple(Ordered)


# each edge must support the whole polygon to reject crossed and degenerate rings
def CheckConvex(Points: tuple[PlaneVector, ...]) -> None:
    Orientation = 0
    for Index, Start in enumerate(Points):
        EndValue = Points[(Index + 1) % len(Points)]
        for OtherIndex, PointValue in enumerate(Points):
            if OtherIndex in (Index, (Index + 1) % len(Points)):
                continue
            SideValue = (EndValue.x - Start.x) * (PointValue.y - Start.y) - (
                EndValue.y - Start.y
            ) * (PointValue.x - Start.x)
            if not IsFinite(SideValue) or abs(SideValue) <= 1e-9:
                raise ValueError("Degenerate Fusion line profile")
            Direction = 1 if SideValue > 0 else -1
            if Orientation and Direction != Orientation:
                raise ValueError("Fusion line profile is crossed or nonconvex")
            Orientation = Direction
