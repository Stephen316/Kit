# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import (
    atan2 as ArcTangent,
    cos as Cosine,
    hypot as Hypotenuse,
    sin as SineValue,
    tau as FullTurn,
)

from convert.geometry.Revolve.SweepVector import DotVector, OffsetVector
from interchange.brep.curves.BrepCurves import CircleCurve
from interchange.brep.topology.BrepTopology import BrepEdge
from interchange.geometry.models.GeometryCurves import ArcGeometry
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.geometry.models.VectorSpace import SpaceVector


# the full carrier plane and signed sweep preserve major arcs and opposite normals
def ArcInPlane(
    Curve: CircleCurve,
    EdgeValue: BrepEdge,
    Origin: SpaceVector,
    PlaneFrame: tuple[SpaceVector, SpaceVector, SpaceVector],
    CircleFrame: tuple[SpaceVector, SpaceVector, SpaceVector],
    Tolerance: float,
) -> tuple[ArcGeometry, bool] | None:
    Normal, PlaneX, PlaneY = PlaneFrame
    CircleAxis, CircleX, CircleY = CircleFrame
    Center = OffsetVector(Curve.center, Origin, -1.0)
    Excursion = Curve.radius * Hypotenuse(
        DotVector(Normal, CircleX), DotVector(Normal, CircleY)
    )
    if not abs(DotVector(Normal, Center)) + Excursion <= Tolerance:
        return None
    Alignment = DotVector(Normal, CircleAxis)
    if abs(abs(Alignment) - 1.0) > 1e-09:
        return None
    Orientation = 1.0 if Alignment > 0.0 else -1.0
    First = EdgeValue.start_parameter
    Finish = EdgeValue.end_parameter
    Sweep = Orientation * (Finish - First)
    if not 0.0 < abs(Sweep) < FullTurn:
        return None
    Parameter = First if Sweep > 0.0 else Finish
    CosValue, SinValue = Cosine(Parameter), SineValue(Parameter)
    StartAngle = (
        ArcTangent(
            CosValue * DotVector(CircleX, PlaneY)
            + SinValue * DotVector(CircleY, PlaneY),
            CosValue * DotVector(CircleX, PlaneX)
            + SinValue * DotVector(CircleY, PlaneX),
        )
        % FullTurn
    )
    Geometry = ArcGeometry(
        PlaneVector(DotVector(Center, PlaneX), DotVector(Center, PlaneY)),
        Curve.radius,
        StartAngle,
        StartAngle + abs(Sweep),
    )
    return Geometry, Sweep < 0.0
