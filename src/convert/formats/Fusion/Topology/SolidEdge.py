# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from convert.formats.Fusion.Topology.AsmEdge.AsmNames import KNameTerms
from convert.formats.Fusion.Topology.AsmEdge.AsmPoints import (
    CheckAsmLine,
    IsAsmNear,
    ReadAsmPoints,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmPrism import (
    AsmPrism,
    ReadAsmBody,
    ReadAsmPrism,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmPrismEdges import (
    AsmPrismEdge,
    ReadAsmEdges,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import ReadAsmTable
from convert.formats.Fusion.Topology.AsmEdge.EdgeOperands import (
    EdgeOperands,
    ReadEdgeRecipe,
)
from convert.formats.Fusion.Topology.AsmEdge.PrismProfile import ReadProfileTags
from convert.formats.Fusion.Topology.AsmEdge.PrismSource import JoinPrismEdges
from interchange.brep.topology.BrepModel import BrepModel
from interchange.geometry.models.Sketch import SketchEntity
from interchange.geometry.models.VectorSpace import SpaceVector


# the recipe chooses a named source edge and orders endpoints before geometry is inspected
def SelectAsmEdge(
    Prism: AsmPrism, Edges: dict[int, AsmPrismEdge], Recipe: EdgeOperands
) -> AsmPrismEdge:
    PairFaces = frozenset(Prism.Names[Value] for Value in Recipe.Faces)
    Candidates = tuple(Value for Value in Edges.values() if Value.Faces == PairFaces)
    if len(Candidates) != 1:
        raise ValueError("Fusion recipe does not identify one named source edge")
    (EdgeValue,) = Candidates
    VertexFaces: dict[int, set[int]] = {}
    for Value in Edges.values():
        for Identity in Value.Vertices:
            VertexFaces.setdefault(Identity, set()).update(Value.Faces)
    EndValues: list[int] = []
    for Group in Recipe.Endpoints:
        Faces = {Prism.Names[Value] for Value in Group}
        Matches = tuple(
            Identity for Identity, Incident in VertexFaces.items() if Incident == Faces
        )
        if len(Matches) != 1:
            raise ValueError(
                "Fusion recipe endpoint lacks unique named vertex incidence"
            )
        EndValues.append(Matches[0])
    if tuple(EndValues) != EdgeValue.Vertices:
        raise ValueError(
            "Fusion recipe ordered endpoints disagree with the named source edge"
        )
    return EdgeValue


# independent source topology and a separate line cache must corroborate the same authored edge
def ReadSolidEdge(
    BlobData: bytes,
    BodyHandle: int,
    Terms: tuple[KNameTerms, ...],
    Payload: bytes,
    SourceModel: BrepModel,
    CachedStart: SpaceVector,
    CachedEnd: SpaceVector,
    Profile: tuple[SketchEntity, ...],
    BodyHandles: frozenset[int],
) -> tuple[str, SpaceVector, SpaceVector]:
    try:
        Recipe = ReadEdgeRecipe(Terms, Payload)
        CurveTags = ReadProfileTags(Profile)
        Table = ReadAsmTable(BlobData)
        BodyId = ReadAsmBody(Table, BodyHandle, BodyHandles)
        Prism = ReadAsmPrism(Table, BodyId, len(CurveTags))
        Edges = ReadAsmEdges(Table, Prism, len(CurveTags))
        Selected = SelectAsmEdge(Prism, Edges, Recipe)
        Points = ReadAsmPoints(Table, Edges, len(CurveTags))
        CheckAsmLine(Table, Selected, Points)
        Joined, Mapped, _ = JoinPrismEdges(SourceModel, Prism, Edges, Points, CurveTags)
        Start, Finish = (Mapped[Identity] for Identity in Selected.Vertices)
        if not IsAsmNear(Start, CachedStart) or not IsAsmNear(Finish, CachedEnd):
            raise ValueError(
                "Fusion selected edge disagrees with its independent line cache"
            )
        return Joined[Selected.Identity].id, Start, Finish
    except (IndexError, KeyError, TypeError, OverflowError) as ErrorInfo:
        raise ValueError(
            "Fusion named source edge incidence is incomplete"
        ) from ErrorInfo


# stable entry point exposes the ordered named source edge resolver
ResolveSolidEdge = ReadSolidEdge
