# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.formats.Fusion.Topology.AsmEdge.AsmPoints import ReadAsmPoints
from convert.formats.Fusion.Topology.AsmEdge.AsmPrism import ReadAsmBody, ReadAsmPrism
from convert.formats.Fusion.Topology.AsmEdge.AsmPrismEdges import ReadAsmEdges
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable
from convert.formats.Fusion.Topology.AsmEdge.PrismCarriers import (
    CheckPrismLine,
    CheckPrismPlane,
)
from convert.formats.Fusion.Topology.AsmEdge.PrismSource import JoinPrismEdges
from interchange.brep.surfaces.BrepSurfaces import PlaneSurface
from interchange.brep.topology.BrepModel import BrepModel


# mapped bodies need named incidence and geometric agreement before supplying a cache witness
def ReadPrismCache(
    Table: AsmTable,
    Handle: int,
    Handles: frozenset[int],
    Expected: BrepModel,
    CurveTags: tuple[int, ...],
) -> int:
    Sides = len(CurveTags)
    if not 3 <= Sides <= 64 or any(Value < 0 for Value in Handles):
        raise ValueError("Unsupported Fusion ASM prism cache inventory")
    try:
        BodyId = ReadAsmBody(Table, Handle, Handles)
        Prism = ReadAsmPrism(Table, BodyId, Sides, AllowIdentity=True)
        Edges = ReadAsmEdges(Table, Prism, Sides)
        Points = ReadAsmPoints(Table, Edges, Sides)
        _, Predicted, Faces = JoinPrismEdges(Expected, Prism, Edges, Points, CurveTags)
        for Value in Edges.values():
            CheckPrismLine(Table, Value, Predicted)
        Surfaces = {Value.id: Value for Value in Expected.surfaces}
        for Identity, FaceValue in Faces.items():
            Surface = Surfaces[FaceValue.surface_id]
            if not isinstance(Surface, PlaneSurface):
                raise ValueError("Missing Fusion ASM prism expected plane")
            CheckPrismPlane(Table, Identity, Surface)
    except (IndexError, KeyError, TypeError, OverflowError) as ErrorInfo:
        raise ValueError("Incomplete Fusion ASM prism cache geometry") from ErrorInfo
    return BodyId
