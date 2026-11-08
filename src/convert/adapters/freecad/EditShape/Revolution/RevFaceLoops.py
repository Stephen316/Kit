# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from collections import Counter
from dataclasses import dataclass as MakeDataClass

from convert.adapters.freecad.EditShape.Prism.PrismRaw import KLocationChain
from convert.adapters.freecad.EditShape.Revolution.RevCarriers import KRevSurface
from convert.adapters.freecad.EditShape.Revolution.RevEdgeMatch import (
    KPlacedKey,
    ReadRevEdgeMut,
    RevEdge,
    RevProof,
)
from convert.adapters.freecad.EditShape.Revolution.RevExpected import KFaceLoop, LoopKey
from convert.adapters.freecad.EditShape.Revolution.RevTrimProof import (
    CheckUvLoop,
    FaceTrim,
    KUvEdge,
)
from convert.geometry.Opencascade import (
    DecodeFailure,
    FaceData,
    OrderWireUses,
    Reference,
)
from interchange.brep.surfaces.BrepSurfaces import PlaneSurface


# separate native use orientation determines the selected seam branch
@MakeDataClass(frozen=True, slots=True)
class RevEdgeUse:
    EdgeValue: RevEdge
    Sense: int


# connectivity is computed on placed native vertices before semantic edge matching
def ReadRevLoopMut(
    Proof: RevProof, WireRef: Reference, FacePlace: KLocationChain
) -> tuple[RevEdgeUse, ...]:
    Record = Proof.RawValue.Records[WireRef.RecordA]
    if (
        Record.KindValue != b"Wi"
        or Record.FlagBits[4] != "1"
        or not 1 <= len(Record.Children) <= 64
        or WireRef.Orientation not in {"+", "-"}
        or any(Value.Orientation not in {"+", "-"} for Value in Record.Children)
    ):
        raise DecodeFailure("unsupported Revolution wire")
    WirePlace = Proof.RawValue.Place(WireRef.KLocation, FacePlace)
    Edges = [ReadRevEdgeMut(Proof, RefValue, WirePlace) for RefValue in Record.Children]
    Vertices = {
        KeyValue: Index
        for Index, KeyValue in enumerate(
            {Value for EdgeValue in Edges for Value in EdgeValue.Vertices}
        )
    }
    EdgeEnds = {
        Index: (Vertices[EdgeValue.Vertices[0]], Vertices[EdgeValue.Vertices[1]])
        for Index, EdgeValue in enumerate(Edges)
    }
    WireSense = 1 if WireRef.Orientation == "+" else -1
    UsesValue = [
        Reference(
            "+" if (RefValue.Orientation == "+") == (WireSense > 0) else "-", Index
        )
        for Index, RefValue in enumerate(Record.Children)
    ]
    Ordered = OrderWireUses(UsesValue, EdgeEnds)
    return tuple(
        RevEdgeUse(Edges[Value.RecordA], 1 if Value.Orientation == "+" else -1)
        for Value in Ordered
    )


# one seam in a full turn may close a periodic face but must never replace an orbit
def ReadLoopKeys(
    Proof: RevProof,
    UsesValue: tuple[RevEdgeUse, ...],
    FaceValue: FaceData,
    FacePlace: KLocationChain,
    Surface: KRevSurface,
    FaceSense: int,
) -> tuple[KFaceLoop, ...]:
    Counts = Counter(Value.EdgeValue.KeyValue for Value in UsesValue)
    Seams = tuple(Value for Value in UsesValue if not Value.EdgeValue.Match)
    IsFull = Proof.Expected.IsFull
    IsPlane = isinstance(Surface, PlaneSurface)
    if any(
        Counts[Value.EdgeValue.KeyValue] != 1
        for Value in UsesValue
        if Value.EdgeValue.Match
    ):
        raise DecodeFailure("duplicate Revolution orbit edge use")
    if not IsFull or IsPlane:
        if Seams:
            raise DecodeFailure("unexpected Revolution seam")
    elif (
        len(UsesValue) != 4
        or len(Seams) != 2
        or Seams[0].EdgeValue.KeyValue != Seams[1].EdgeValue.KeyValue
        or Seams[0].Sense == Seams[1].Sense
    ):
        raise DecodeFailure("invalid Revolution periodic seam")
    EndsValue = ReadUvEdges(Proof, UsesValue, FaceValue, FacePlace)
    if not IsPlane:
        CheckUvLoop(EndsValue, IsFull)
    RingValue = tuple(
        (Value.EdgeValue.Match, Value.EdgeValue.Sense * Value.Sense * FaceSense)
        for Value in (UsesValue if FaceSense > 0 else UsesValue[::-1])
        if Value.EdgeValue.Match
    )
    return tuple((Value,) for Value in RingValue) if Seams else (LoopKey(RingValue),)


# every explicit current trim is checked even when a planar face could infer it
def ReadUvEdges(
    Proof: RevProof,
    UsesValue: tuple[RevEdgeUse, ...],
    FaceValue: FaceData,
    FacePlace: KLocationChain,
) -> tuple[KUvEdge, ...]:
    EndsValue = tuple(
        FaceTrim(
            Proof.RawValue,
            Value.EdgeValue,
            FaceValue,
            FacePlace,
            Value.Sense,
            not Value.EdgeValue.Match,
        )
        for Value in UsesValue
    )
    return tuple(Value for Value in EndsValue if Value is not None)


# physical edge uses must pair in opposite directions across the closed shell
def ReadEdgeCounts(
    UsesValue: tuple[RevEdgeUse, ...], FaceSense: int
) -> Counter[tuple[KPlacedKey, int]]:
    return Counter(
        (Value.EdgeValue.KeyValue, Value.Sense * FaceSense) for Value in UsesValue
    )
