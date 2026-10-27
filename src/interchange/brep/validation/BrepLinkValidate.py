# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from typing import Mapping as TypeMap

from interchange.brep.topology.BrepTopology import BrepCoedge, BrepEdge


# connectivity checks ensure loops and wires traverse incident vertices consistently
def IsCoedgeLink(
    CoedgeIds: tuple[str, ...],
    CoedgeById: TypeMap[str, BrepCoedge],
    EdgeById: TypeMap[str, BrepEdge],
    IsClosed: bool,
) -> bool:
    CoedgeUses: list[tuple[str, str]] = []
    for CoedgeId in CoedgeIds:
        CoedgeValue = CoedgeById.get(CoedgeId)
        if CoedgeValue is None:
            return False
        EdgeValue = EdgeById.get(CoedgeValue.EdgeId)
        if EdgeValue is None:
            return False
        StartId, EndId = EdgeValue.StartVertexId, EdgeValue.EndVertexId
        DirectedUse = (EndId, StartId) if CoedgeValue.IsReversed else (StartId, EndId)
        CoedgeUses.append(DirectedUse)
    if not CoedgeUses:
        return False
    LinkPairs = zip(CoedgeUses, CoedgeUses[1:])
    if any(LeftUse[1] != RightUse[0] for LeftUse, RightUse in LinkPairs):
        return False
    return not IsClosed or CoedgeUses[-1][1] == CoedgeUses[0][0]
