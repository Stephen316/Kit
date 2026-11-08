# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.adapters.freecad.EditShape.Sketch.SavedWireData import ReadSavedWire
from convert.adapters.freecad.EditShape.Sketch.WireMatch import KSketchCurve
from convert.adapters.freecad.EditShape.Sketch.WireProof import (
    CheckPathMut,
    CheckVertMut,
)
from convert.geometry.Extrude.Polygon.PrismFrame import PlacePrismPoint
from convert.geometry.Opencascade import DecodeFailure
from interchange.geometry.models.GeometryCurves import (
    ArcGeometry,
    CircleGeometry,
    LineGeometry,
    PointGeometry,
)
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector

# analytic sketch archives remain bounded before reading native shape tokens
KMaxSketchBytes = 262_144


# construction geometry is omitted from the same visible wire exported by freecad
def ReadVisible(
    SketchValue: Sketch, FrameValue: Transform
) -> tuple[list[KSketchCurve], list[SpaceVector]]:
    ClosedIds = {
        Identity
        for Profile in SketchValue.closed_profile_entity_ids
        for Identity in Profile
    }
    Curves: list[KSketchCurve] = []
    Points: list[SpaceVector] = []
    for Entity in SketchValue.entities:
        if Entity.construction or (ClosedIds and Entity.id not in ClosedIds):
            continue
        Geometry = Entity.geometry
        if isinstance(Geometry, PointGeometry):
            Points.append(PlacePrismPoint(FrameValue, Geometry.point, 0.0))
        elif isinstance(Geometry, (ArcGeometry, CircleGeometry, LineGeometry)):
            Curves.append(Geometry)
        else:
            raise DecodeFailure("unsupported saved sketch cache geometry")
    return Curves, Points


# independent wire cache geometry must corroborate every visible point and curve
def IsSketchCache(
    ShapeData: bytes,
    SketchValue: Sketch,
    FrameValue: Transform,
    ClosedWire: bool = False,
    *,
    AllowPcurves: bool = False,
    DirectedLines: bool = False,
) -> bool:
    if len(ShapeData) > KMaxSketchBytes:
        return False
    try:
        Curves, Points = ReadVisible(SketchValue, FrameValue)
        if DirectedLines and any(
            not isinstance(Curve, LineGeometry) for Curve in Curves
        ):
            return False
        if AllowPcurves and (
            not ClosedWire
            or Points
            or any(not isinstance(Curve, LineGeometry) for Curve in Curves)
        ):
            return False
        if not ShapeData:
            return not ClosedWire and not Curves and not Points
        DataValue = ReadSavedWire(
            ShapeData, len(Curves), len(Points), AllowPcurves=AllowPcurves
        )
        RootValue = DataValue.Records[DataValue.RootRef.RecordA]
        if ClosedWire and (
            RootValue.KindValue != b"Wi" or RootValue.FlagBits[4] != "1"
        ):
            return False
        Children = (
            RootValue.Children if RootValue.KindValue == b"Co" else (DataValue.RootRef,)
        )
        if len({Child.RecordA for Child in Children}) != len(Children):
            return False
        UsedEdges: set[int] = set()
        for Child in Children:
            KindValue = DataValue.Records[Child.RecordA].KindValue
            if Child.Orientation != "+":
                return False
            if KindValue == b"Wi":
                CheckPathMut(
                    DataValue, Child, Curves, FrameValue, UsedEdges, DirectedLines
                )
            elif KindValue == b"Ve":
                CheckVertMut(DataValue, Child, Points)
            else:
                return False
        return not Curves and not Points
    except (
        DecodeFailure,
        IndexError,
        KeyError,
        TypeError,
        ValueError,
        OverflowError,
        RecursionError,
    ):
        return False
