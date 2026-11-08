# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from collections import Counter

from convert.adapters.freecad.EditShape.CylinderRims import KPositionTolerance
from convert.adapters.freecad.EditShape.Prism.PrismRaw import KLocationChain
from convert.adapters.freecad.EditShape.Revolution.RevEdgeMatch import (
    KPlacedKey,
    RevProof,
)
from convert.adapters.freecad.EditShape.Revolution.RevExpected import ReadRevExpected
from convert.adapters.freecad.EditShape.Revolution.RevFaceLoops import (
    ReadEdgeCounts,
    ReadLoopKeys,
    ReadRevLoopMut,
)
from convert.adapters.freecad.EditShape.Revolution.RevFaceMatch import IsRevCarrier
from convert.adapters.freecad.EditShape.Revolution.RevRaw import ReadRevRaw
from convert.adapters.freecad.EditShape.Revolution.RevTrimProof import CheckRevTrims
from convert.geometry.Opencascade import (
    AssertReachable,
    DecodeFailure,
    EdgeData,
    FaceData,
    Reference,
)
from interchange.brep.topology.BrepModel import BrepModel

# bounded native topology permits repeated edits without allocating untrusted archive data
KMaxRevolveBytes = 262_144


# native saved shapes independently corroborate the edited profile and angular controls
def IsEditRevolve(ShapeData: bytes, Expected: BrepModel) -> bool:
    if not ShapeData or len(ShapeData) > KMaxRevolveBytes:
        return False
    try:
        Target = ReadRevExpected(Expected)
        SeamCount = len(Target.Faces) if Target.IsFull else 0
        EdgeLimit = len(Target.Edges) + SeamCount
        ShapeLimit = (
            len(Target.Points) + EdgeLimit + len(Expected.loops) + len(Target.Faces) + 2
        )
        Proof = RevProof(ReadRevRaw(ShapeData, EdgeLimit, ShapeLimit), Target)
        CheckRevShape(Proof)
    except (KeyError, OverflowError, ValueError):
        return False
    return True


# a single closed shell must own all placed faces and preserve exact edge sharing
def CheckRevShape(Proof: RevProof) -> None:
    RawValue = Proof.RawValue
    RootRecord = RawValue.Records[RawValue.RootRef.RecordA]
    if RootRecord.KindValue != b"So" or len(RootRecord.Children) != 1:
        raise DecodeFailure("Revolution root is not a single solid")
    (ShellRef,) = RootRecord.Children
    ShellValue = RawValue.Records[ShellRef.RecordA]
    if (
        ShellValue.KindValue != b"Sh"
        or ShellValue.FlagBits[4] != "1"
        or ShellRef.Orientation not in {"+", "-"}
        or len(ShellValue.Children) != len(Proof.Expected.Faces)
    ):
        raise DecodeFailure("Revolution solid does not have one closed shell")
    ShellPlace = RawValue.Place(
        ShellRef.KLocation, RawValue.Place(RawValue.RootRef.KLocation)
    )
    FaceIds: set[int] = set()
    Counts: Counter[tuple[KPlacedKey, int]] = Counter()
    for FaceRef in ShellValue.Children:
        FaceSense = 1 if FaceRef.Orientation == ShellRef.Orientation else -1
        FaceId, UsesValue = CheckRevFaceMut(Proof, FaceRef, ShellPlace, FaceSense)
        FaceIds.add(FaceId)
        Counts.update(UsesValue)
    if (
        len(FaceIds) != len(Proof.Expected.Faces)
        or set(Proof.MatchedEdges) != set(Proof.Expected.Edges)
        or set(Proof.MatchedVerts) != set(Proof.Expected.Points)
        or any(
            Counts[KeyValue, SenseValue] != 1
            for KeyValue in Proof.Edges
            for SenseValue in (1, -1)
        )
    ):
        raise DecodeFailure(
            "Revolution closed topology disagrees with reconstructed model"
        )
    CheckRawProof(Proof)


# each face must own the same carrier and oriented boundaries as the rebuilt solid
def CheckRevFaceMut(
    Proof: RevProof, FaceRef: Reference, ShellPlace: KLocationChain, FaceSense: int
) -> tuple[int, Counter[tuple[KPlacedKey, int]]]:
    RawValue = Proof.RawValue
    FacePlace = RawValue.Place(FaceRef.KLocation, ShellPlace)
    Record = RawValue.Records[FaceRef.RecordA]
    FaceValue = Record.GeometryA
    if (
        not isinstance(FaceValue, FaceData)
        or FaceValue.Natural
        or FaceValue.Tolerance > KPositionTolerance
        or FaceRef.Orientation not in {"+", "-"}
        or not 1 <= len(Record.Children) <= 2
    ):
        raise DecodeFailure("unsupported Revolution face")
    Surface = RawValue.Surfaces[FaceValue.Surface - 1]
    Matrix = RawValue.Matrix(FacePlace, FaceValue.KLocation)
    Rings = []
    Counts: Counter[tuple[KPlacedKey, int]] = Counter()
    for WireRef in Record.Children:
        UsesValue = ReadRevLoopMut(Proof, WireRef, FacePlace)
        Rings.extend(
            ReadLoopKeys(Proof, UsesValue, FaceValue, FacePlace, Surface, FaceSense)
        )
        Counts.update(ReadEdgeCounts(UsesValue, FaceSense))
    Loops = tuple(sorted(Rings))
    Matches = [
        Index
        for Index, Value in enumerate(Proof.Expected.Faces)
        if Value.Loops == Loops
        and IsRevCarrier(Proof.Expected, Value, Surface, Matrix, FaceSense)
    ]
    if len(Matches) != 1:
        raise DecodeFailure("Revolution face carrier or boundary disagreement")
    return Matches[0], Counts


# extra topology and unattached geometric entries cannot hide in a valid solid cache
def CheckRawProof(Proof: RevProof) -> None:
    RawValue = Proof.RawValue
    Records = RawValue.Records
    AssertReachable(
        RawValue.RootRef.RecordA,
        {
            Index: tuple(Child.RecordA for Child in Value.Children)
            for Index, Value in Records.items()
        },
        {Index: Value.KindValue for Index, Value in Records.items()},
    )
    EdgeIds = {Index for Index, _ in Proof.Edges}
    if EdgeIds != set(RawValue.Trims):
        raise DecodeFailure("unreachable Revolution edge")
    Curves = {
        Geometry.Curve
        for Record in Records.values()
        if isinstance(Geometry := Record.GeometryA, EdgeData)
    }
    Surfaces = {
        Geometry.Surface
        for Record in Records.values()
        if isinstance(Geometry := Record.GeometryA, FaceData)
    }
    Surfaces.update(CheckRevTrims(RawValue, EdgeIds))
    if len(Curves) != len(RawValue.Curves) or len(Surfaces) != len(RawValue.Surfaces):
        raise DecodeFailure("unreachable Revolution analytic carrier")
