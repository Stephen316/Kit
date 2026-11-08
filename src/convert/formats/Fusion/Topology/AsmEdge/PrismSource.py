# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.formats.Fusion.Topology.AsmEdge.AsmPoints import IsAsmNear
from convert.formats.Fusion.Topology.AsmEdge.AsmPrism import AsmPrism
from convert.formats.Fusion.Topology.AsmEdge.AsmPrismEdges import AsmPrismEdge
from convert.formats.Fusion.Topology.AsmEdge.PrismJoin import JoinPrismVerts
from interchange.brep.curves.BrepCurves import LineCurve
from interchange.brep.surfaces.BrepSurfaces import PlaneSurface
from interchange.brep.topology.BrepModel import BrepModel
from interchange.brep.topology.BrepTopology import BrepEdge, BrepFace
from interchange.geometry.models.VectorSpace import SpaceVector


# a complete neutral face edge inventory checks cap and wall incidence after identity joins
def JoinPrismFaces(
    Model: BrepModel, Prism: AsmPrism, JoinedEdges: dict[int, BrepEdge]
) -> dict[int, BrepFace]:
    UseValues = {Value.id: Value.edge_id for Value in Model.coedges}
    Loops = {Value.id: Value.coedge_ids for Value in Model.loops}
    if any(len(Value.loop_ids) != 1 for Value in Model.faces):
        raise ValueError("Fusion source prism neutral face bounds are unresolved")
    Neutral = {
        frozenset(UseValues[Identity] for Identity in Loops[Value.loop_ids[0]]): Value
        for Value in Model.faces
    }
    Native = {
        Identity: frozenset(JoinedEdges[Value.EdgeId].id for Value in RingValue)
        for Identity, RingValue in Prism.Rings.items()
    }
    if len(Neutral) != len(Model.faces) or set(Native.values()) != Neutral.keys():
        raise ValueError(
            "Fusion ASM prism faces disagree with neutral cap and side incidence"
        )
    return {Identity: Neutral[EdgeIds] for Identity, EdgeIds in Native.items()}


# only a verified complete prism can bridge named native edges to generated neutral ids
def JoinPrismEdges(
    Model: BrepModel,
    Prism: AsmPrism,
    Edges: dict[int, AsmPrismEdge],
    Points: dict[int, SpaceVector],
    CurveTags: tuple[int, ...],
) -> tuple[dict[int, BrepEdge], dict[int, SpaceVector], dict[int, BrepFace]]:
    Sides = len(CurveTags)
    if (
        len(Model.bodies) != 1
        or len(Model.regions) != 1
        or not Model.regions[0].solid
        or len(Model.shells) != 1
        or not Model.shells[0].closed
        or len(Model.faces) != Sides + 2
        or len(Model.vertices) != 2 * Sides
        or len(Model.edges) != 3 * Sides
        or any(not isinstance(Value, LineCurve) for Value in Model.curves)
        or any(not isinstance(Value, PlaneSurface) for Value in Model.surfaces)
    ):
        raise ValueError(
            "Fusion edge source neutral body is not a complete straight prism"
        )
    IdentityMap = JoinPrismVerts(Edges, Model.edges, CurveTags)
    Neutral = {Value.id: Value.point for Value in Model.vertices}
    if (
        IdentityMap.keys() != Points.keys()
        or set(IdentityMap.values()) != Neutral.keys()
    ):
        raise ValueError("Fusion ASM prism vertex inventory disagrees with its source")
    Mapped = {Identity: Neutral[Value] for Identity, Value in IdentityMap.items()}
    if any(
        not IsAsmNear(Mapped[Identity], Point) for Identity, Point in Points.items()
    ):
        raise ValueError(
            "Fusion ASM prism vertices disagree with reconstructed source geometry"
        )
    ByPair = {
        frozenset((Value.start_vertex_id, Value.end_vertex_id)): Value
        for Value in Model.edges
    }
    JoinedEdges = {
        Identity: ByPair[
            frozenset(IdentityMap[Vertex] for Vertex in EdgeValue.Vertices)
        ]
        for Identity, EdgeValue in Edges.items()
    }
    if len({Value.id for Value in JoinedEdges.values()}) != len(Model.edges):
        raise ValueError("Fusion ASM prism edge correspondence is ambiguous")
    return JoinedEdges, Mapped, JoinPrismFaces(Model, Prism, JoinedEdges)
