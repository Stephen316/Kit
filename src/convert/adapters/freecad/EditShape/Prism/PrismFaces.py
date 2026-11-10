# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from convert.adapters.freecad.EditShape.CylinderRims import (
    IsParallel,
    KPositionTolerance,
)
from convert.adapters.freecad.EditShape.Prism.PrismExpected import RingKey
from convert.adapters.freecad.EditShape.Prism.PrismProof import PrismProof, ReadEdgeMut
from convert.adapters.freecad.EditShape.Prism.PrismRaw import KLocationChain
from convert.adapters.freecad.EditShape.Prism.PrismTrim import CheckTrimBind
from convert.adapters.freecad.EditShape.TrimGeometry import SurfaceHand
from convert.geometry.Opencascade import (
    ApplyDirection,
    DecodeFailure,
    EdgeData,
    FaceData,
    LocationPoint,
    Reference,
)
from convert.geometry.Revolve.SweepVector import DotVector
from interchange.brep.curves.BrepCurves import LineCurve
from interchange.brep.surfaces.BrepSurfaces import PlaneSurface
from interchange.geometry.models.VectorSpace import SpaceVector


# native storage may list edge uses out of traversal order but must prove one simple cycle
def ReadFaceLoopMut(
    Proof: PrismProof, WireRef: Reference, FacePlace: KLocationChain
) -> tuple[int, ...]:
    WirePlace = Proof.RawValue.Place(WireRef, FacePlace)
    EdgeRefs = Proof.RawValue.Records[WireRef.RecordA].Children
    EdgeUses = tuple(ReadEdgeMut(Proof, RefValue, WirePlace) for RefValue in EdgeRefs)
    NextEdges = dict(EdgeUses)
    if len(NextEdges) != len(EdgeRefs):
        raise DecodeFailure("prism wire branches or repeats an edge")
    First = EdgeUses[0][0]
    Indices = [First]
    for _ in range(len(EdgeRefs) - 1):
        Following = NextEdges[Indices[-1]]
        if Following in Indices:
            raise DecodeFailure("prism wire repeats a corner")
        Indices.append(Following)
    if NextEdges[Indices[-1]] != First:
        raise DecodeFailure("prism wire is open")
    return tuple(Indices)


# proper shell and face senses must produce the same outward loop and plane
def CheckFaceMut(
    Proof: PrismProof,
    ShellRef: Reference,
    FaceRef: Reference,
    ShellPlace: KLocationChain,
) -> tuple[int, ...]:
    FacePlace = Proof.RawValue.Place(FaceRef, ShellPlace)
    Record = Proof.RawValue.Records[FaceRef.RecordA]
    (WireRef,) = Record.Children
    LoopValue = ReadFaceLoopMut(Proof, WireRef, FacePlace)
    FaceSense = 1 if FaceRef.Orientation == ShellRef.Orientation else -1
    Reverse = (FaceSense < 0) != (WireRef.Orientation == "-")
    KeyValue = RingKey(LoopValue[::-1] if Reverse else LoopValue)
    Normal = Proof.Expected.Faces.get(KeyValue)
    Geometry = Record.GeometryA
    if (
        Normal is None
        or not isinstance(Geometry, FaceData)
        or Geometry.Natural
        or Geometry.Tolerance > KPositionTolerance
    ):
        raise DecodeFailure("prism face does not match an outward boundary")
    Surface = Proof.RawValue.Surfaces[Geometry.Surface - 1]
    if not isinstance(Surface, PlaneSurface):
        raise DecodeFailure("prism face must use a planar carrier")
    Matrix = Proof.RawValue.Matrix(FacePlace, Geometry.KLocation)
    AxisValue = ApplyDirection(Matrix, Surface.normal)
    Center = LocationPoint(Matrix, Surface.origin)
    if (
        not IsParallel(AxisValue, Normal)
        or DotVector(AxisValue, Normal) * FaceSense * SurfaceHand(Surface) <= 0.0
    ):
        raise DecodeFailure("prism face carrier has the wrong outward sense")
    if any(
        not IsOnPlane(Proof.Expected.Points[Index], Center, AxisValue)
        for Index in KeyValue
    ):
        raise DecodeFailure("prism face carrier misses its boundary")
    if Proof.RawValue.Pcurves:
        CheckFaceTrims(Proof, WireRef, Geometry, Surface)
    return KeyValue


# a signed distance comparison verifies the entire planar boundary through its vertices
def IsOnPlane(Point: SpaceVector, Center: SpaceVector, AxisValue: SpaceVector) -> bool:
    Offset = SpaceVector(Point.x - Center.x, Point.y - Center.y, Point.z - Center.z)
    return abs(DotVector(Offset, AxisValue)) <= KPositionTolerance


# kit seed trims are explicitly attached to the same faces as the native edge uses
def CheckFaceTrims(
    Proof: PrismProof, WireRef: Reference, Geometry: FaceData, Surface: PlaneSurface
) -> None:
    RawValue = Proof.RawValue
    for RefValue in RawValue.Records[WireRef.RecordA].Children:
        EdgeValue = RawValue.Records[RefValue.RecordA].GeometryA
        if not isinstance(EdgeValue, EdgeData):
            raise DecodeFailure("prism trim references a non-edge")
        Curve = RawValue.Curves[EdgeValue.Curve - 1]
        if not isinstance(Curve, LineCurve):
            raise DecodeFailure("prism trim references a non-line")
        CheckTrimBind(
            RawValue.Bindings[RefValue.RecordA],
            RawValue.Pcurves,
            EdgeValue,
            Geometry,
            Curve,
            Surface,
        )
