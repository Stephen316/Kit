from dataclasses import dataclass as MakeDataClass, field as DataField
from math import tau as FullTurn

from convert.adapters.freecad.EditShape.CylinderRims import (
    IsNearPoint,
    IsParallel,
    KAngleTolerance,
    KPositionTolerance,
)
from convert.adapters.freecad.EditShape.Prism.PrismRaw import KLocationChain
from convert.adapters.freecad.EditShape.Revolution.RevCarriers import (
    CurvePoint,
    KRevCurve,
)
from convert.adapters.freecad.EditShape.Revolution.RevExpected import RevExpected
from convert.adapters.freecad.EditShape.Revolution.RevRaw import RevRaw
from convert.geometry.Opencascade import (
    ApplyDirection,
    DecodeFailure,
    EdgeData,
    LocationPoint,
    Reference,
    VertexData,
)
from convert.geometry.Revolve.SweepVector import DotVector
from interchange.brep.curves.BrepCurves import CircleCurve, LineCurve
from interchange.brep.topology.BrepTopology import BrepEdge
from interchange.geometry.models.VectorSpace import SpaceVector

# native locations distinguish separate instances of a shared edge or vertex
KPlacedKey = tuple[int, KLocationChain]


# a placed edge binds its analytic range and topological endpoints independently
@MakeDataClass(frozen=True, slots=True)
class RevEdge:
    KeyValue: KPlacedKey
    Geometry: EdgeData
    Curve: KRevCurve
    Vertices: tuple[KPlacedKey, KPlacedKey]
    Points: tuple[SpaceVector, SpaceVector]
    Match: str
    Sense: int


# matching identities are shared across faces so duplicate seams or split edges fail
@MakeDataClass(slots=True)
class RevProof:
    RawValue: RevRaw
    Expected: RevExpected
    Edges: dict[KPlacedKey, RevEdge] = DataField(
        default_factory=dict[KPlacedKey, RevEdge]
    )
    MatchedEdges: dict[str, KPlacedKey] = DataField(
        default_factory=dict[str, KPlacedKey]
    )
    MatchedVerts: dict[str, KPlacedKey] = DataField(
        default_factory=dict[str, KPlacedKey]
    )


# placed native curve frames retain their original parameter direction
def PlaceRevCurve(Curve: KRevCurve, Matrix: tuple[float, ...]) -> KRevCurve:
    if isinstance(Curve, LineCurve):
        return LineCurve(
            Curve.id,
            LocationPoint(Matrix, Curve.origin),
            ApplyDirection(Matrix, Curve.direction),
        )
    return CircleCurve(
        Curve.id,
        LocationPoint(Matrix, Curve.center),
        ApplyDirection(Matrix, Curve.axis),
        ApplyDirection(Matrix, Curve.reference_direction),
        Curve.radius,
    )


# stored edge vertices must be shared native occurrences with coherent signed parameters
def ReadRevVerts(
    RawValue: RevRaw, RefsValue: tuple[Reference, ...], ChainValue: KLocationChain
) -> tuple[tuple[KPlacedKey, SpaceVector], tuple[KPlacedKey, SpaceVector]]:
    if len(RefsValue) != 2 or {Value.Orientation for Value in RefsValue} != {"+", "-"}:
        raise DecodeFailure("unsupported Revolution edge endpoint roles")
    First, Second = RefsValue
    if First.Orientation == "-":
        First, Second = Second, First
    return ReadRevVertex(RawValue, First, ChainValue), ReadRevVertex(
        RawValue, Second, ChainValue
    )


# points use their located topology rather than matching loose coordinate values
def ReadRevVertex(
    RawValue: RevRaw, RefValue: Reference, Parent: KLocationChain
) -> tuple[KPlacedKey, SpaceVector]:
    ChainValue = RawValue.Place(RefValue.KLocation, Parent)
    Record = RawValue.Records[RefValue.RecordA]
    Vertex = Record.GeometryA
    if (
        Record.Children
        or not isinstance(Vertex, VertexData)
        or Vertex.Tolerance > KPositionTolerance
    ):
        raise DecodeFailure("invalid Revolution vertex")
    return (RefValue.RecordA, ChainValue), LocationPoint(
        RawValue.Matrix(ChainValue), Vertex.Point
    )


# curve spans and interior circle phases distinguish complementary angular sectors
def MatchRevEdge(
    Curve: KRevCurve,
    Range: tuple[float, float],
    Points: tuple[SpaceVector, SpaceVector],
    Expected: RevExpected,
    EdgeValue: BrepEdge,
) -> int:
    Target = Expected.Curves[EdgeValue.curve_id]
    if isinstance(Curve, CircleCurve) and isinstance(Target, CircleCurve):
        AxisSign = CircleSense(Curve, Target)
        TargetWidth = abs(EdgeValue.end_parameter - EdgeValue.start_parameter)
        if not AxisSign or abs(Range[1] - Range[0] - TargetWidth) > KAngleTolerance:
            return 0
        Sense = (
            AxisSign
            if EdgeValue.start_parameter < EdgeValue.end_parameter
            else -AxisSign
        )
        if Expected.IsFull:
            return Sense if abs(TargetWidth - FullTurn) <= KAngleTolerance else 0
        if not IsNearPoint(
            CurvePoint(Curve, (Range[0] + Range[1]) / 2.0),
            CurvePoint(
                Target, (EdgeValue.start_parameter + EdgeValue.end_parameter) / 2.0
            ),
        ):
            return 0
        return Sense if IsEdgeEnds(Points, Expected, EdgeValue, Sense) else 0
    if isinstance(Curve, LineCurve) and isinstance(Target, LineCurve):
        for Sense in (1, -1):
            if IsEdgeEnds(Points, Expected, EdgeValue, Sense):
                return Sense
    return 0


# closed orbit seams may move in phase but their axes centers and radii are immutable
def CircleSense(First: CircleCurve, Second: CircleCurve) -> int:
    if (
        not IsNearPoint(First.center, Second.center)
        or abs(First.radius - Second.radius) > KPositionTolerance
        or not IsParallel(First.axis, Second.axis)
    ):
        return 0
    return 1 if DotVector(First.axis, Second.axis) > 0.0 else -1


# directed endpoints distinguish shared ring edges from disconnected trim substitutes
def IsEdgeEnds(
    Points: tuple[SpaceVector, SpaceVector],
    Expected: RevExpected,
    EdgeValue: BrepEdge,
    Sense: int,
) -> bool:
    First, Second = (
        Expected.Points[EdgeValue.start_vertex_id],
        Expected.Points[EdgeValue.end_vertex_id],
    )
    if Sense < 0:
        First, Second = Second, First
    return IsNearPoint(First, Points[0]) and IsNearPoint(Second, Points[1])


# expected edge and vertex ids must each own exactly one placed native occurrence
def BindRevEdgeMut(Proof: RevProof, EdgeValue: RevEdge) -> None:
    if EdgeValue.Match in Proof.MatchedEdges:
        raise DecodeFailure("duplicate Revolution edge")
    Proof.MatchedEdges[EdgeValue.Match] = EdgeValue.KeyValue
    Expected = Proof.Expected.Edges[EdgeValue.Match]
    Vertices = EdgeValue.Vertices if EdgeValue.Sense > 0 else EdgeValue.Vertices[::-1]
    for Index, Placed in zip(
        (Expected.start_vertex_id, Expected.end_vertex_id), Vertices, strict=True
    ):
        Prior = Proof.MatchedVerts.get(Index)
        if Prior is not None:
            if Prior != Placed:
                raise DecodeFailure("split Revolution vertex")
        elif Placed in Proof.MatchedVerts.values():
            raise DecodeFailure("collapsed Revolution vertex")
        else:
            Proof.MatchedVerts[Index] = Placed


# partial edges match exactly while full turn generator seams are checked at face scope
def ReadRevEdgeMut(
    Proof: RevProof, RefValue: Reference, Parent: KLocationChain
) -> RevEdge:
    RawValue = Proof.RawValue
    ChainValue = RawValue.Place(RefValue.KLocation, Parent)
    KeyValue = (RefValue.RecordA, ChainValue)
    Cached = Proof.Edges.get(KeyValue)
    if Cached is not None:
        return Cached
    EdgeValue = MakeRevEdge(Proof, KeyValue)
    if EdgeValue.Match:
        BindRevEdgeMut(Proof, EdgeValue)
    Proof.Edges[KeyValue] = EdgeValue
    return EdgeValue


# finite native edge geometry must terminate at the actual placed vertex records
def MakeRevEdge(Proof: RevProof, KeyValue: KPlacedKey) -> RevEdge:
    RawValue = Proof.RawValue
    Index, ChainValue = KeyValue
    Record = RawValue.Records[Index]
    Geometry = Record.GeometryA
    if (
        not isinstance(Geometry, EdgeData)
        or Geometry.Tolerance > KPositionTolerance
        or Geometry.FirstValue >= Geometry.LastValue
    ):
        raise DecodeFailure("invalid Revolution edge")
    Matrix = RawValue.Matrix(ChainValue, Geometry.KLocation)
    Curve = PlaceRevCurve(RawValue.Curves[Geometry.Curve - 1], Matrix)
    (FirstKey, FirstPoint), (SecondKey, SecondPoint) = ReadRevVerts(
        RawValue, Record.Children, ChainValue
    )
    Range = (Geometry.FirstValue, Geometry.LastValue)
    Points = (FirstPoint, SecondPoint)
    if any(
        not IsNearPoint(Point, CurvePoint(Curve, Param))
        for Point, Param in zip(Points, Range, strict=True)
    ):
        raise DecodeFailure("Revolution edge endpoint range disagreement")
    Matches = [
        (EdgeValue.id, SenseValue)
        for EdgeValue in Proof.Expected.Edges.values()
        if (SenseValue := MatchRevEdge(Curve, Range, Points, Proof.Expected, EdgeValue))
    ]
    if len(Matches) == 1:
        Match, Sense = Matches[0]
    elif (
        not Matches
        and Proof.Expected.IsFull
        and isinstance(Curve, LineCurve)
        and FirstKey != SecondKey
    ):
        Match, Sense = "", 1
    else:
        raise DecodeFailure("unqualified Revolution edge span")
    return RevEdge(
        KeyValue, Geometry, Curve, (FirstKey, SecondKey), Points, Match, Sense
    )
