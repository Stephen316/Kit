# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isclose as IsClose, isfinite as IsFinite
from struct import unpack_from as UnpackFrom

from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.ParamProjection import ParamOrigin as RecordOrigin
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Sketches.GeometryAttrs import ReadGeomAttrs
from convert.formats.Fusion.Sketches.SketchCircular import IsCircleFrame, ReadSketchArc
from convert.formats.Fusion.Sketches.SketchPointRef import ReadPointRef
from interchange.core.Common import FreezeMapping
from interchange.enums.EnumGeometry import GeometryKind
from interchange.geometry.models.GeometryCurves import (
    ArcGeometry,
    CircleGeometry,
    LineGeometry,
    PointGeometry,
)
from interchange.geometry.models.Sketch import SketchEntity
from interchange.geometry.models.VectorPlane import PlaneVector

# registered primitive classes delimit the supported sketch geometry records
KSketchKinds = {
    "C2CEDAE7-1716-47C1-B7B1-07B70081D0FB": GeometryKind.KPoint,
    "DCA267ED-D615-4934-B64F-AD805E8003E2": GeometryKind.KLine,
    "F0130424-8B7E-4092-93C9-1CA807482534": GeometryKind.KCircle,
}


# point records prove planar coordinates before supplying curve endpoint evidence
def ReadPoint(BodyValue: bytes, StartOffset: int) -> PlaneVector:
    Values = tuple(
        float(Value) * 10 for Value in UnpackFrom("<3d", BodyValue, StartOffset)
    )
    if not all(map(IsFinite, Values)) or abs(Values[2]) > 1e-8:
        raise ValueError("Nonplanar or non-finite Fusion sketch point")
    return PlaneVector(Values[0], Values[1])


# comparison of stored endpoint copies catches inconsistent native geometry
def IsSamePoint(First: PlaneVector, Second: PlaneVector) -> bool:
    return IsClose(First.x, Second.x, abs_tol=1e-8) and IsClose(
        First.y, Second.y, abs_tol=1e-8
    )


# native primitive values and point backlinks must agree before projection
def ReadPrimitive(
    BodyValue: bytes, SpanValue: RecordSpan, Points: dict[int, PlaneVector]
) -> SketchEntity:
    KindValue = KSketchKinds[SpanValue.ClassGuid]
    Cursor = MetaCursor(BodyValue)
    Props = ReadGeomAttrs(Cursor)
    Offset = Cursor.Offset
    Width = len(BodyValue) - Offset
    Genesis = Props.get("EntityGenesis")
    if Genesis not in (0, 2, 64, 128, 130, 256, 258, 512):
        raise ValueError("Unsupported Fusion sketch primitive genesis")
    Fixed = False
    Construction = False
    Geometry: PointGeometry | LineGeometry | CircleGeometry | ArcGeometry
    Extras: dict[str, object] = {}
    if KindValue == GeometryKind.KPoint:
        TagValue = Props.get("pt_tag")
        if Width != 99 or not isinstance(TagValue, int):
            raise ValueError("Unsupported Fusion sketch point layout")
        Geometry = PointGeometry(ReadPoint(BodyValue, Offset + 19))
    else:
        TagValue = Props.get("crv_primary_id")
        Expected = (171,) if KindValue == GeometryKind.KLine else (162, 182)
        if (
            Width not in Expected
            or not isinstance(TagValue, int)
            or Props.get("crv_secondary_id") != 0
        ):
            raise ValueError("Unsupported Fusion sketch curve layout")
        if Width == 182:
            Geometry, Extras = ReadSketchArc(BodyValue, Offset, Points)
            KindValue = GeometryKind.KArcGeometry
        else:
            Origin = ReadPoint(BodyValue, Offset)
            TargetId, Target = ReadPointRef(BodyValue, Offset + 96, Points)
            if KindValue == GeometryKind.KLine:
                StartId, Start = ReadPointRef(BodyValue, Offset + 107, Points)
                Delta = ReadPoint(BodyValue, Offset + 24)
                EndValue = PlaneVector(Origin.x + Delta.x, Origin.y + Delta.y)
                if not IsSamePoint(Origin, Start) or not IsSamePoint(EndValue, Target):
                    raise ValueError("Fusion line endpoint cache disagrees")
                Geometry = LineGeometry(Start, Target)
                Extras = {"fusion.line_native_point_ids": (StartId, TargetId)}
            else:
                Radius = float(UnpackFrom("<d", BodyValue, Offset + 72)[0]) * 10
                Normal = UnpackFrom("<3d", BodyValue, Offset + 24)
                RefAxis = UnpackFrom("<3d", BodyValue, Offset + 48)
                if (
                    not IsFinite(Radius)
                    or Radius <= 0.0
                    or not IsSamePoint(Origin, Target)
                    or not IsCircleFrame(Normal, RefAxis)
                ):
                    raise ValueError("Invalid Fusion sketch circle geometry")
                Geometry = CircleGeometry(Target, Radius)
                Extras = {
                    "fusion.circle_native_normal": Normal,
                    "fusion.circle_native_reference_axis": RefAxis,
                }
        FixedFlag = UnpackFrom("<I", BodyValue, len(BodyValue) - 51)[0]
        ConstructionFlag = UnpackFrom("<I", BodyValue, len(BodyValue) - 46)[0]
        if FixedFlag not in (0, 1) or ConstructionFlag not in (0, 1):
            raise ValueError("Unsupported Fusion sketch curve state")
        Fixed, Construction = bool(FixedFlag), bool(ConstructionFlag)
    return SketchEntity(
        id=f"fusion-sketch-entity-{SpanValue.ObjectId}",
        kind=KindValue,
        geometry=Geometry,
        fixed=Fixed,
        construction=Construction,
        provenance=RecordOrigin(SpanValue),
        attributes=FreezeMapping(
            {"fusion.entity_tag": TagValue, "fusion.entity_genesis": Genesis, **Extras}
        ),
    )
