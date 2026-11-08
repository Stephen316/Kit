# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import dataclass as MakeDataClass
from math import hypot as Hypot

from convert.adapters.freecad.EditShape.CylinderRims import KPositionTolerance
from convert.geometry.Extrude.Polygon.PrismFrame import CheckPrismFrame, PlacePrismPoint
from convert.geometry.Extrude.Polygon.PrismRing import MeasureRing, ReadPrismRing
from convert.geometry.Revolve.SweepVector import CrossVector
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.geometry.models.VectorSpace import SpaceVector


# face winding keys ignore the native wire start without losing directed topology
def RingKey(Indices: tuple[int, ...]) -> tuple[int, ...]:
    Start = Indices.index(min(Indices))
    return Indices[Start:] + Indices[:Start]


# positive outward caps and side loops supply one unique expected face per boundary
@MakeDataClass(frozen=True, slots=True)
class ExpectedPrism:
    Points: tuple[SpaceVector, ...]
    Faces: dict[tuple[int, ...], SpaceVector]
    Edges: set[frozenset[int]]


# signed stations and local outward normals derive solely from the edited sketch
def ExpectedShape(
    Frame: Transform, Profile: tuple[PlaneVector, ...], DistanceMm: float
) -> ExpectedPrism:
    CheckPrismFrame(Frame)
    Following = Profile[1:] + Profile[:1]
    Lines = tuple(
        LineGeometry(First, Second) for First, Second in zip(Profile, Following)
    )
    RingValue, _, _ = MeasureRing(ReadPrismRing(Lines))
    Sides = len(RingValue)
    AxisZ = Frame.z_axis
    Points = tuple(
        PlacePrismPoint(Frame, Point, Height)
        for Height in (min(0.0, DistanceMm), max(0.0, DistanceMm))
        for Point in RingValue
    )
    Faces = {
        RingKey(tuple(reversed(range(Sides)))): SpaceVector(
            -AxisZ.x, -AxisZ.y, -AxisZ.z
        ),
        tuple(range(Sides, 2 * Sides)): AxisZ,
    }
    for Index, First in enumerate(RingValue):
        NextIndex = (Index + 1) % Sides
        Second = RingValue[NextIndex]
        DeltaX, DeltaY = Second.x - First.x, Second.y - First.y
        Length = Hypot(DeltaX, DeltaY)
        if Length <= 2.0 * KPositionTolerance:
            raise ValueError("prism side is below shape resolution")
        AxisX, AxisY = Frame.x_axis, Frame.y_axis
        SideVector = SpaceVector(
            (DeltaX * AxisX.x + DeltaY * AxisY.x) / Length,
            (DeltaX * AxisX.y + DeltaY * AxisY.y) / Length,
            (DeltaX * AxisX.z + DeltaY * AxisY.z) / Length,
        )
        Faces[RingKey((Index, NextIndex, NextIndex + Sides, Index + Sides))] = (
            CrossVector(SideVector, AxisZ)
        )
    Edges = {
        frozenset((First, Second))
        for Indices in Faces
        for First, Second in zip(Indices, Indices[1:] + Indices[:1])
    }
    return ExpectedPrism(Points, Faces, Edges)
