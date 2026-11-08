# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from typing import TypeVar

from convert.formats.Fusion.Topology.AsmEdge.AsmPrismEdges import AsmPrismEdge
from interchange.brep.topology.BrepTopology import BrepEdge

# source and neutral rim endpoints use independent identity types
KVertexId = TypeVar("KVertexId", int, str)


# each profile point is the unique meeting of two explicitly named source curves
def ReadRimKeys(
    Tagged: dict[int, tuple[KVertexId, KVertexId]],
) -> dict[frozenset[int], KVertexId]:
    ByVertex: dict[KVertexId, set[int]] = {}
    for TagValue, EndValues in Tagged.items():
        for Identity in EndValues:
            ByVertex.setdefault(Identity, set()).add(TagValue)
    if len(ByVertex) != len(Tagged) or any(
        len(Value) != 2 for Value in ByVertex.values()
    ):
        raise ValueError("Fusion prism profile rim is not a closed tagged cycle")
    Result = {frozenset(Value): Identity for Identity, Value in ByVertex.items()}
    if len(Result) != len(ByVertex):
        raise ValueError("Fusion prism tagged vertex keys are ambiguous")
    return Result


# a rail has one endpoint on the already identified original profile rim
def ReadPrismRails(
    Vertices: set[KVertexId], Pairs: tuple[tuple[KVertexId, KVertexId], ...]
) -> dict[KVertexId, KVertexId]:
    Result: dict[KVertexId, KVertexId] = {}
    for Start, Finish in Pairs:
        if (Start in Vertices) == (Finish in Vertices):
            continue
        if Start not in Vertices:
            Start, Finish = Finish, Start
        if Start in Result:
            raise ValueError("Fusion source prism has an ambiguous rail")
        Result[Start] = Finish
    if Result.keys() != Vertices or len(set(Result.values())) != len(Vertices):
        raise ValueError("Fusion source prism rail inventory disagrees")
    return Result


# named profile rims and topological rails give a coordinate independent vertex bijection
def JoinPrismVerts(
    Edges: dict[int, AsmPrismEdge],
    Neutral: tuple[BrepEdge, ...],
    CurveTags: tuple[int, ...],
) -> dict[int, str]:
    Sides = len(CurveTags)
    Tagged = tuple(Value for Value in Edges.values() if Value.ProfileTag is not None)
    NativeRim = {Value.ProfileTag: Value.Vertices for Value in Tagged}
    if len(Tagged) != Sides or NativeRim.keys() != set(CurveTags):
        raise ValueError("Fusion ASM tags do not bind the complete source profile")
    NeutralRim = {
        TagValue: (Value.start_vertex_id, Value.end_vertex_id)
        for TagValue, Value in zip(CurveTags, Neutral[:Sides], strict=True)
    }
    NativeKeys = ReadRimKeys(NativeRim)
    NeutralKeys = ReadRimKeys(NeutralRim)
    if NativeKeys.keys() != NeutralKeys.keys():
        raise ValueError("Fusion ASM rim joins disagree with the source profile")
    Joined = {
        Identity: NeutralKeys[KeyValue] for KeyValue, Identity in NativeKeys.items()
    }
    NativeRails = ReadPrismRails(
        set(Joined), tuple(Value.Vertices for Value in Edges.values())
    )
    NeutralRails = ReadPrismRails(
        set(Joined.values()),
        tuple((Value.start_vertex_id, Value.end_vertex_id) for Value in Neutral),
    )
    return {
        **Joined,
        **{
            Other: NeutralRails[Joined[Identity]]
            for Identity, Other in NativeRails.items()
        },
    }
