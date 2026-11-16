from dataclasses import dataclass as MakeDataClass
from typing import Mapping as KMapping

from convert.Formats.Fusion.BrepCodec.Journal.Spline.Capped.CageGraph import (
    CageGraph,
)
from convert.Formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleRows import (
    KPoleRow,
    MixRows,
)
from convert.Formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface

# the face key shape must stay shared so spline pole reconstruction uses one contract for compatible values
KFaceKey = tuple[int, ...]

# edge key must remain consistent across callers so neighboring patches retain consistent subdivision boundaries
KEdgeKey = frozenset[int]

# the half key shape must stay shared so spline pole reconstruction uses one contract for compatible values
KHalfKey = tuple[int, int]

# dart kind must remain consistent across callers so neighboring patches retain consistent subdivision boundaries
KDartKind = 1

# crease kind must remain consistent across callers so neighboring patches retain consistent subdivision boundaries
KCreaseKind = 2

# corner kind must remain consistent across callers so neighboring patches retain consistent subdivision boundaries
KCornerKind = 3


# pole mesh needs an explicit state contract so neighboring patches retain consistent subdivision boundaries
@MakeDataClass(frozen=True, slots=True)
class PoleMesh:
    Faces: KMapping[KFaceKey, tuple[int, ...]]
    Values: KMapping[int, KPoleRow]
    Sharp: frozenset[KEdgeKey]
    Corners: frozenset[int]
    Halves: KMapping[KHalfKey, tuple[KFaceKey, int]]
    Touch: KMapping[int, tuple[KFaceKey, ...]]
    Around: KMapping[int, frozenset[int]]


# the mesh operation needs a consistent construction rule so neighboring patches retain consistent subdivision boundaries
def BuildMesh(
    Faces: dict[KFaceKey, tuple[int, ...]],
    Values: dict[int, KPoleRow],
    Sharp: frozenset[KEdgeKey],
    Corners: frozenset[int],
) -> PoleMesh:
    Halves: dict[KHalfKey, tuple[KFaceKey, int]] = {}
    Touch: dict[int, list[KFaceKey]] = {}
    for FaceKey, LoopValue in Faces.items():
        for Corner, Vertex in enumerate(LoopValue):
            Halves[(Vertex, LoopValue[(Corner + 1) % len(LoopValue)])] = (
                FaceKey,
                Corner,
            )
            Touch.setdefault(Vertex, []).append(FaceKey)
    Around: dict[int, set[int]] = {}
    OpenEdges: set[KEdgeKey] = set()
    for Start, Final in Halves:
        Around.setdefault(Start, set()).add(Final)
        Around.setdefault(Final, set()).add(Start)
        if (Final, Start) not in Halves:
            OpenEdges.add(frozenset((Start, Final)))
    return PoleMesh(
        Faces,
        Values,
        Sharp | frozenset(OpenEdges),
        Corners,
        Halves,
        {Vertex: tuple(FaceKeys) for Vertex, FaceKeys in Touch.items()},
        {Vertex: frozenset(Others) for Vertex, Others in Around.items()},
    )


# primary grips needs an explicit validity boundary so neighboring patches retain consistent subdivision boundaries
def PrimaryGrips(Surface: TsplineSurface) -> dict[int, int]:
    if len(Surface.Grips) > len(Surface.Topology.Vertices):
        raise ValueError("Fusion Form pole engine leaves compound grips to grid paths")
    if Surface.Mapping is None:
        return {}
    return {
        Owner.VertexIndex: GripIndex
        for GripIndex, Owner in enumerate(Surface.Mapping.Owners)
        if Owner.IsPrimary
    }


# the mesh from cage contract needs a shared interpretation so neighboring patches retain consistent subdivision boundaries
def MeshFromCage(Surface: TsplineSurface, Graph: CageGraph) -> PoleMesh:
    GripOf = PrimaryGrips(Surface)
    Faces: dict[KFaceKey, tuple[int, ...]] = {
        (FaceIndex,): tuple(Graph.Links[LinkIndex].VertexIndex for LinkIndex in Loops)
        for FaceIndex, Loops in enumerate(Graph.Loops)
    }
    Values = {
        Vertex: {GripOf.get(Vertex, Vertex): 1.0}
        for Vertex in range(len(Surface.Topology.Vertices))
    }
    Sharp = frozenset(
        frozenset((Graph.Links[LinkIndex].VertexIndex, Graph.Heads[LinkIndex]))
        for LinkIndex in range(len(Graph.Links))
        if Graph.Creased[LinkIndex]
    )
    return BuildMesh(Faces, Values, Sharp, frozenset())


# the sharp ends contract needs a shared interpretation so neighboring patches retain consistent subdivision boundaries
def SharpEnds(MeshValue: PoleMesh, Vertex: int) -> tuple[int, ...]:
    return tuple(
        Other
        for Other in sorted(MeshValue.Around[Vertex])
        if frozenset((Vertex, Other)) in MeshValue.Sharp
    )


# the vertex kind contract needs a shared interpretation so neighboring patches retain consistent subdivision boundaries
def VertexKind(MeshValue: PoleMesh, Vertex: int) -> int:
    Count = len(SharpEnds(MeshValue, Vertex))
    if Vertex in MeshValue.Corners or Count >= KCornerKind:
        return KCornerKind
    return Count


# the face mean contract needs a shared interpretation so neighboring patches retain consistent subdivision boundaries
def FaceMean(MeshValue: PoleMesh, FaceKey: KFaceKey) -> KPoleRow:
    LoopValue = MeshValue.Faces[FaceKey]
    Share = 1.0 / len(LoopValue)
    return MixRows((Share, MeshValue.Values[Vertex]) for Vertex in LoopValue)


# the edge point contract needs a shared interpretation so neighboring patches retain consistent subdivision boundaries
def EdgePoint(MeshValue: PoleMesh, Start: int, Final: int) -> KPoleRow:
    Middle = MixRows(((0.5, MeshValue.Values[Start]), (0.5, MeshValue.Values[Final])))
    if frozenset((Start, Final)) in MeshValue.Sharp:
        return Middle
    LeftFace = MeshValue.Halves[(Start, Final)][0]
    RightFace = MeshValue.Halves[(Final, Start)][0]
    return MixRows(
        (
            (0.5, Middle),
            (0.25, FaceMean(MeshValue, LeftFace)),
            (0.25, FaceMean(MeshValue, RightFace)),
        )
    )


# the vertex point contract needs a shared interpretation so neighboring patches retain consistent subdivision boundaries
def VertexPoint(MeshValue: PoleMesh, Vertex: int) -> KPoleRow:
    KindValue = VertexKind(MeshValue, Vertex)
    OwnRow = MeshValue.Values[Vertex]
    if KindValue == KCornerKind:
        return OwnRow
    if KindValue == KCreaseKind:
        EndPoints = SharpEnds(MeshValue, Vertex)
        return MixRows(
            (
                (0.75, OwnRow),
                (0.125, MeshValue.Values[EndPoints[0]]),
                (0.125, MeshValue.Values[EndPoints[1]]),
            )
        )
    Valence = len(MeshValue.Around[Vertex])
    FaceKeys = MeshValue.Touch[Vertex]
    FaceShare = 1.0 / (Valence * len(FaceKeys))
    EdgeShare = 1.0 / (Valence * Valence)
    Parts = [(FaceShare, FaceMean(MeshValue, FaceKey)) for FaceKey in FaceKeys]
    Parts += [
        (EdgeShare, MeshValue.Values[Other]) for Other in MeshValue.Around[Vertex]
    ]
    Parts.append(((Valence - 2.0) / Valence, OwnRow))
    return MixRows(Parts)
