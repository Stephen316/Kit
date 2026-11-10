# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.adapters.freecad.EditExtSolid import BuildEditSolid, KEditProfile
from interchange.brep.topology.BrepModel import BrepModel
from interchange.features.FeatureBody import DesignBody
from interchange.geometry.models.Transform import Transform


# a saved shape can seed the live feature only when it matches the current sketch and depth
def IsEditExtBody(
    BodyValue: DesignBody,
    BrepValue: BrepModel | None,
    Profile: KEditProfile,
    Frame: Transform,
    DepthMm: float,
) -> bool:
    if BrepValue is None or BodyValue.topology.valid is not True:
        return False
    Model, Volume, AreaValue, Bounds = BuildEditSolid(
        BodyValue.id, Frame, Profile, DepthMm
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
