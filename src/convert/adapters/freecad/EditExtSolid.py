# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.geometry.Extrude.Circular.CircularExtrude import BuildCircular
from convert.geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from interchange.brep.topology.BrepModel import BrepModel
from interchange.geometry.models.BoundingBox import BoundingBox
from interchange.geometry.models.GeometryCurves import CircleGeometry, LineGeometry
from interchange.geometry.models.Transform import Transform

# source qualification and readback rebuild accept the same exact solid profile families
KEditProfile = CircleGeometry | tuple[LineGeometry, ...]


# unchanged circle and line ring builders preserve the original neutral body identifiers
def BuildEditSolid(
    BodyId: str, FrameValue: Transform, Profile: KEditProfile, DepthMm: float
) -> tuple[BrepModel, float, float, BoundingBox]:
    Lower, Upper = sorted((0.0, DepthMm))
    if isinstance(Profile, CircleGeometry):
        return BuildCircular(
            BodyId, FrameValue, Profile, Lower, Upper, Profile.radius, Profile.radius
        )
    return BuildPrism(BodyId, FrameValue, Profile, Lower, Upper)
