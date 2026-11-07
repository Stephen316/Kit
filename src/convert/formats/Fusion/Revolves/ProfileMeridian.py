# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.Revolves.MeridianSense import ChooseMeridian
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# both angular and plane limits use the same occupied line profile half plane
def CalcMeridian(
    SketchFrame: Transform,
    ProfileLines: tuple[LineGeometry, ...],
    AxisOrigin: SpaceVector,
    AxisDirection: SpaceVector,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    if len(ProfileLines) not in (3, 4):
        raise ValueError("Fusion Revolve requires a three or four line profile")
    Points = tuple(
        Point
        for LineValue in ProfileLines
        for Point in (LineValue.start, LineValue.end)
    )
    return ChooseMeridian(SketchFrame, Points, AxisOrigin, AxisDirection)
