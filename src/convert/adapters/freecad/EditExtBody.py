# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.geometry.Extrude.Circular.CircularExtrude import BuildCircular
from interchange.brep.topology.BrepModel import BrepModel
from interchange.features.FeatureBody import DesignBody
from interchange.geometry.models.GeometryCurves import CircleGeometry
from interchange.geometry.models.Transform import Transform


# a saved shape can seed the live feature only when it matches the current sketch and depth
def IsEditExtBody(
    BodyValue: DesignBody,
    BrepValue: BrepModel | None,
    Profile: CircleGeometry,
    Frame: Transform,
    DepthMm: float,
) -> bool:
    if BrepValue is None or BodyValue.topology.valid is not True:
        return False
    Lower, Upper = sorted((0.0, DepthMm))
    Model, Volume, AreaValue, Bounds = BuildCircular(
        BodyValue.id, Frame, Profile, Lower, Upper, Profile.radius, Profile.radius
    )
    Topology = BodyValue.topology
    return BrepValue == Model and (
        Topology.solid_count,
        Topology.shell_count,
        Topology.face_count,
        Topology.edge_count,
        Topology.vertex_count,
        Topology.volume,
        Topology.surface_area,
        Topology.bounding_box,
    ) == (
        len(Model.regions),
        len(Model.shells),
        len(Model.faces),
        len(Model.edges),
        len(Model.vertices),
        Volume,
        AreaValue,
        Bounds,
    )
