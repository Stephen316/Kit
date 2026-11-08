# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isfinite as IsFinite

from convert.geometry.Extrude.Polygon.PrismFrame import CheckPrismFrame
from convert.geometry.Extrude.Trimmed.TrimBounds import GetTrimBounds
from convert.geometry.Extrude.Trimmed.TrimEdges import BuildTrimEdges
from convert.geometry.Extrude.Trimmed.TrimFaces import BuildTrimFaces
from convert.geometry.Extrude.Trimmed.TrimMeasures import MeasureTrim
from convert.geometry.Extrude.Trimmed.TrimOperand import ReadOperand
from convert.geometry.Extrude.Trimmed.TrimOrder import (
    JoinTolerance,
    MatchTrimEnds,
    WalkTrimRing,
)
from convert.geometry.Extrude.Trimmed.TrimSimple import CheckTrimSimple
from convert.geometry.Revolve.SweepModel import BuildSweepModel
from interchange.brep.topology.BrepModel import BrepModel
from interchange.geometry.models.BoundingBox import BoundingBox
from interchange.geometry.models.GeometryCurves import ArcGeometry, LineGeometry
from interchange.geometry.models.Transform import Transform


# a simple bounded ring supplies exact untapered geometry and component space measures
def BuildTrimPrism(
    BodyId: str,
    FrameValue: Transform,
    Parts: tuple[LineGeometry | ArcGeometry, ...],
    LowerMm: float,
    UpperMm: float,
) -> tuple[BrepModel, float, float, BoundingBox]:
    Height = UpperMm - LowerMm
    if (
        not isinstance(BodyId, str)
        or not BodyId.strip()
        or not (IsFinite(Height) and Height > 0.0)
    ):
        raise ValueError(
            "Extrude trim requires a body identity and finite positive depth"
        )
    if not 2 <= len(Parts) <= 64:
        raise ValueError("Extrude trim requires two to sixty four profile portions")
    CheckPrismFrame(FrameValue)
    Operands = tuple(ReadOperand(PartValue) for PartValue in Parts)
    Tolerance = JoinTolerance(Operands)
    Endpoints = tuple(
        Point for Value in Operands for Point in (Value.Start, Value.Finish)
    )
    Matches = MatchTrimEnds(Endpoints, Tolerance)
    CheckTrimSimple(Operands, Endpoints, Matches, Tolerance)
    Points, RingUses = WalkTrimRing(Operands, Endpoints, Matches)
    AreaValue, Perimeter = MeasureTrim(Points, RingUses)
    if AreaValue < 0.0:
        Points = Points[:1] + Points[:0:-1]
        RingUses = tuple(
            (Operand, not Reverse) for Operand, Reverse in reversed(RingUses)
        )
    Volume = abs(AreaValue) * Height
    SurfaceArea = 2.0 * abs(AreaValue) + Perimeter * Height
    if not (IsFinite(Volume) and Volume > 0.0 and IsFinite(SurfaceArea)):
        raise ValueError("Extrude trim solid measures exceed floating range")
    Prefix = f"{BodyId}-trim"
    Vertices, Curves, Edges = BuildTrimEdges(
        Prefix, FrameValue, Points, RingUses, LowerMm, UpperMm, Tolerance
    )
    Surfaces, Faces, Loops, Coedges = BuildTrimFaces(
        Prefix, FrameValue, Curves, Edges, RingUses, LowerMm, UpperMm
    )
    Model = BuildSweepModel(
        BodyId, Prefix, Curves, Surfaces, Vertices, Edges, Faces, Loops, Coedges
    )
    return (
        Model,
        Volume,
        SurfaceArea,
        GetTrimBounds(Operands, FrameValue, LowerMm, UpperMm),
    )
