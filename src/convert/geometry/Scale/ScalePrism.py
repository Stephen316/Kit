# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isfinite as IsFinite

from convert.geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from interchange.brep.topology.BrepModel import BrepModel
from interchange.geometry.models.BoundingBox import BoundingBox
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.geometry.models.VectorSpace import SpaceVector


# diagonal factors preserve straight sides and the horizontal extrusion frame
def BuildScalePrism(
    BodyId: str,
    Profile: tuple[LineGeometry, ...],
    FrameValue: Transform,
    Depth: float,
    Factors: SpaceVector,
    Center: SpaceVector,
) -> tuple[BrepModel, float, float, BoundingBox]:
    if (FrameValue.x_axis, FrameValue.y_axis, FrameValue.z_axis) != (
        SpaceVector(1, 0, 0),
        SpaceVector(0, 1, 0),
        SpaceVector(0, 0, 1),
    ):
        raise ValueError("scaled prism requires a component aligned source frame")
    if any(
        not IsFinite(Factor) or Factor <= 0
        for Factor in (Factors.x, Factors.y, Factors.z)
    ):
        raise ValueError("scaled prism requires finite positive diagonal factors")
    Origin = FrameValue.origin
    ScaledFrame = Transform(
        origin=SpaceVector(
            Center.x + Factors.x * (Origin.x - Center.x),
            Center.y + Factors.y * (Origin.y - Center.y),
            Center.z + Factors.z * (Origin.z - Center.z),
        )
    )
    ScaledProfile = tuple(
        LineGeometry(
            PlaneVector(Line.start.x * Factors.x, Line.start.y * Factors.y),
            PlaneVector(Line.end.x * Factors.x, Line.end.y * Factors.y),
        )
        for Line in Profile
    )
    ScaledDepth = Depth * Factors.z
    return BuildPrism(
        BodyId, ScaledFrame, ScaledProfile, min(0.0, ScaledDepth), max(0.0, ScaledDepth)
    )
