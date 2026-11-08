# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import replace as ReplaceData
from math import hypot as Hypot
from math import isfinite as IsFinite

from convert.adapters.freecad.EditShape.CylinderRims import KPositionTolerance
from convert.adapters.freecad.EditShape.Scale.ScaleSpan import ScaleSpan
from convert.geometry.Opencascade import DecodeFailure, EdgeData, ShapeRecord
from convert.geometry.Revolve.SweepVector import OffsetVector
from interchange.brep.curves.BrepCurves import LineCurve
from interchange.geometry.models.VectorSpace import SpaceVector


# converting verified affine spans to exact distance parameters lets the prism proof stay shared
def ScaleLines(
    Curves: tuple[ScaleSpan, ...], Records: dict[int, ShapeRecord]
) -> tuple[tuple[LineCurve, ...], dict[int, ShapeRecord]]:
    Lines = []
    Lengths = []
    for Index, SpanValue in enumerate(Curves, 1):
        Origin = SpaceVector(*SpanValue.Start)
        EndPoint = SpaceVector(*SpanValue.EndPoint)
        Delta = OffsetVector(EndPoint, Origin, -1.0)
        Length = Hypot(Delta.x, Delta.y, Delta.z)
        if not IsFinite(Length) or Length <= 2.0 * KPositionTolerance:
            raise DecodeFailure("invalid Scale spline edge length")
        Direction = SpaceVector(Delta.x / Length, Delta.y / Length, Delta.z / Length)
        Lines.append(LineCurve(f"freecad:scale:curve:{Index}", Origin, Direction))
        Lengths.append(Length)
    Updated = dict(Records)
    for Index, Record in Records.items():
        EdgeValue = Record.GeometryA
        if isinstance(EdgeValue, EdgeData):
            if (EdgeValue.FirstValue, EdgeValue.LastValue) != Curves[
                EdgeValue.Curve - 1
            ].Domain:
                raise DecodeFailure("Scale spline edge range disagrees with its curve")
            Updated[Index] = ReplaceData(
                Record,
                GeometryA=ReplaceData(
                    EdgeValue, FirstValue=0.0, LastValue=Lengths[EdgeValue.Curve - 1]
                ),
            )
    return tuple(Lines), Updated
