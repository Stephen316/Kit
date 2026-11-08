# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.adapters.freecad.EditShape.CylinderRims import (
    IsNearPoint,
    KPositionTolerance,
)
from convert.adapters.freecad.EditShape.Sketch.SavedWireData import SavedWireData
from convert.adapters.freecad.EditShape.Sketch.WireEdge import ReadSavedEdge
from convert.adapters.freecad.EditShape.Sketch.WireMatch import IsSameEdge, KSketchCurve
from convert.geometry.Opencascade import DecodeFailure, Reference, VertexData
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# each ordered wire consumes complete authored curve geometry and connects matching vertices
def CheckPathMut(
    DataValue: SavedWireData,
    WireRef: Reference,
    Expected: list[KSketchCurve],
    FrameValue: Transform,
    UsedEdges: set[int],
    DirectedLines: bool = False,
) -> None:
    WireValue = DataValue.Records[WireRef.RecordA]
    if not WireValue.Children or WireRef.Orientation != "+":
        raise DecodeFailure("invalid saved sketch wire")
    VertexPairs = []
    for EdgeRef in WireValue.Children:
        if DirectedLines and EdgeRef.Orientation != "+":
            raise DecodeFailure("saved sketch axis edge orientation changed")
        if EdgeRef.RecordA in UsedEdges:
            raise DecodeFailure("ambiguous saved sketch cache edge")
        UsedEdges.add(EdgeRef.RecordA)
        EdgeValue = ReadSavedEdge(DataValue, EdgeRef)
        Match = next(
            (
                Index
                for Index, Value in enumerate(Expected)
                if IsSameEdge(EdgeValue, Value, FrameValue, DirectedLines)
            ),
            None,
        )
        if Match is None:
            raise DecodeFailure("saved sketch cache edge disagrees with geometry")
        Expected.pop(Match)
        VertexPairs.append(EdgeValue.VertexIds)
    if any(
        Earlier[1] != Right[0] for Earlier, Right in zip(VertexPairs, VertexPairs[1:])
    ) or (WireValue.FlagBits[4] == "1") != (VertexPairs[0][0] == VertexPairs[-1][1]):
        raise DecodeFailure("saved sketch cache wire connectivity disagrees")


# free vertices are an independent multiset even when coordinates coincide with curve endpoints
def CheckVertMut(
    DataValue: SavedWireData, VertexRef: Reference, Expected: list[SpaceVector]
) -> None:
    Record = DataValue.Records[VertexRef.RecordA]
    Vertex = Record.GeometryA
    if (
        Record.Children
        or not isinstance(Vertex, VertexData)
        or not 0 <= Vertex.Tolerance <= KPositionTolerance
    ):
        raise DecodeFailure("invalid saved sketch cache point")
    Match = next(
        (
            Index
            for Index, Value in enumerate(Expected)
            if IsNearPoint(Value, Vertex.Point)
        ),
        None,
    )
    if Match is None:
        raise DecodeFailure("saved sketch cache point disagrees with geometry")
    Expected.pop(Match)
