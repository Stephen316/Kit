# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.freecad.EditShape.CylinderRims import IsNearPoint
from convert.adapters.freecad.EditShape.Prism.PrismRaw import KLocationChain, PrismRaw
from convert.geometry.Opencascade import (
    DecodeFailure,
    LocationPoint,
    Reference,
    VertexData,
)
from interchange.geometry.models.VectorSpace import SpaceVector

# native edge selection needs the exact directed endpoints at its saved subelement number
KPrismLink = tuple[int, SpaceVector, SpaceVector]


# first seen located edge identities reproduce freecad subelement numbering
def PrismEdgeRefs(
    Raw: PrismRaw,
) -> list[tuple[Reference, KLocationChain, bool]]:
    (Shell,) = Raw.Records[Raw.RootRef.RecordA].Children
    ShellPlace = Raw.Place(Shell, Raw.Place(Raw.RootRef))
    Seen: set[tuple[int, KLocationChain]] = set()
    Edges = []
    for Face in Raw.Records[Shell.RecordA].Children:
        (Wire,) = Raw.Records[Face.RecordA].Children
        WirePlace = Raw.Place(Wire, Raw.Place(Face, ShellPlace))
        Prefix = (
            (Shell.Orientation == "-")
            ^ (Face.Orientation == "-")
            ^ (Wire.Orientation == "-")
        )
        for Edge in Raw.Records[Wire.RecordA].Children:
            Place = Raw.Place(Edge, WirePlace)
            KeyValue = Edge.RecordA, Place
            if KeyValue not in Seen:
                Seen.add(KeyValue)
                Edges.append((Edge, Place, Prefix ^ (Edge.Orientation == "-")))
    return Edges


# a changed native record order cannot silently redirect a correct looking solid
def CheckPrismLink(Raw: PrismRaw, Link: KPrismLink) -> None:
    Slot, Start, Finish = Link
    Refs = PrismEdgeRefs(Raw)
    if not 0 < Slot <= len(Refs):
        raise DecodeFailure("saved prism edge slot is missing")
    Edge, Place, Reverse = Refs[Slot - 1]
    Vertices = Raw.Records[Edge.RecordA].Children
    Points = {}
    for RefValue in Vertices:
        DataValue = Raw.Records[RefValue.RecordA].GeometryA
        if not isinstance(DataValue, VertexData):
            raise DecodeFailure("saved prism edge has no bounded vertex")
        Points[RefValue.Orientation] = LocationPoint(
            Raw.Matrix(Raw.Place(RefValue, Place)), DataValue.Point
        )
    if set(Points) != {"+", "-"}:
        raise DecodeFailure("saved prism edge has no directed endpoints")
    Head, Tail = ("-", "+") if Reverse else ("+", "-")
    if not IsNearPoint(Points[Head], Start) or not IsNearPoint(Points[Tail], Finish):
        raise DecodeFailure("saved prism selected edge slot disagrees with its axis")
