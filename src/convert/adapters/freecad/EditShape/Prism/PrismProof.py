# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import dataclass as MakeDataClass, field as DataField

from convert.adapters.freecad.EditShape.CylinderRims import (
    IsNearPoint,
    KPositionTolerance,
)
from convert.adapters.freecad.EditShape.Prism.PrismExpected import ExpectedPrism
from convert.adapters.freecad.EditShape.Prism.PrismRaw import KLocationChain, PrismRaw
from convert.geometry.Opencascade import (
    DecodeFailure,
    EdgeData,
    LocationPoint,
    Reference,
    VertexData,
)
from convert.geometry.Revolve.SweepVector import OffsetVector
from interchange.brep.curves.BrepCurves import LineCurve

# the same native record at another location is a different topological instance
KPlacedKey = tuple[int, KLocationChain]


# a bijection prevents geometric coincidence from hiding split vertices and duplicated edges
@MakeDataClass(slots=True)
class PrismProof:
    RawValue: PrismRaw
    Expected: ExpectedPrism
    Vertices: dict[KPlacedKey, int] = DataField(default_factory=dict)
    Edges: dict[KPlacedKey, tuple[int, int]] = DataField(default_factory=dict)


# each placed native vertex must resolve exactly one expected ring corner
def ReadVertexMut(
    Proof: PrismProof, RefValue: Reference, Parent: KLocationChain
) -> int:
    ChainValue = Proof.RawValue.Place(RefValue, Parent)
    VertexKey = (RefValue.RecordA, ChainValue)
    if VertexKey not in Proof.Vertices:
        Record = Proof.RawValue.Records[RefValue.RecordA].GeometryA
        if not isinstance(Record, VertexData) or Record.Tolerance > KPositionTolerance:
            raise DecodeFailure("invalid prism vertex")
        World = LocationPoint(Proof.RawValue.Matrix(ChainValue), Record.Point)
        Matches = [
            Index
            for Index, Point in enumerate(Proof.Expected.Points)
            if IsNearPoint(World, Point)
        ]
        if len(Matches) != 1 or Matches[0] in Proof.Vertices.values():
            raise DecodeFailure("prism vertex does not match a unique corner")
        Proof.Vertices[VertexKey] = Matches[0]
    return Proof.Vertices[VertexKey]


# line parameter endpoints and real vertex references must define the same edge
def ReadEdgeMut(
    Proof: PrismProof, RefValue: Reference, Parent: KLocationChain
) -> tuple[int, int]:
    ChainValue = Proof.RawValue.Place(RefValue, Parent)
    EdgeKey = (RefValue.RecordA, ChainValue)
    if EdgeKey not in Proof.Edges:
        Record = Proof.RawValue.Records[RefValue.RecordA]
        Geometry = Record.GeometryA
        if (
            not isinstance(Geometry, EdgeData)
            or Geometry.Tolerance > KPositionTolerance
        ):
            raise DecodeFailure("invalid prism edge")
        if {Value.Orientation for Value in Record.Children} != {"+", "-"}:
            raise DecodeFailure("invalid prism edge vertex senses")
        First, Second = Record.Children
        if First.Orientation == "-":
            First, Second = Second, First
        Start = ReadVertexMut(Proof, First, ChainValue)
        EndPoint = ReadVertexMut(Proof, Second, ChainValue)
        CheckEdgeGeom(Proof, Geometry, ChainValue, Start, EndPoint)
        Proof.Edges[EdgeKey] = (Start, EndPoint)
    Start, EndPoint = Proof.Edges[EdgeKey]
    return (Start, EndPoint) if RefValue.Orientation == "+" else (EndPoint, Start)


# analytic carrier endpoints corroborate both finite edge range and declared incidence
def CheckEdgeGeom(
    Proof: PrismProof,
    Geometry: EdgeData,
    ChainValue: KLocationChain,
    Start: int,
    EndPoint: int,
) -> None:
    Curve = Proof.RawValue.Curves[Geometry.Curve - 1]
    if (
        not isinstance(Curve, LineCurve)
        or Geometry.FirstValue >= Geometry.LastValue
        or frozenset((Start, EndPoint)) not in Proof.Expected.Edges
    ):
        raise DecodeFailure("unsupported prism edge carrier")
    Matrix = Proof.RawValue.Matrix(ChainValue, Geometry.KLocation)
    for Index, Parameter in (
        (Start, Geometry.FirstValue),
        (EndPoint, Geometry.LastValue),
    ):
        Point = LocationPoint(
            Matrix, OffsetVector(Curve.origin, Curve.direction, Parameter)
        )
        if not IsNearPoint(Point, Proof.Expected.Points[Index]):
            raise DecodeFailure("prism edge endpoints disagree with its vertices")
