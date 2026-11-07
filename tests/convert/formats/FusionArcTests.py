# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from math import pi as Pi
from struct import pack as Pack

from pytest import approx as Approx
from pytest import raises as Raises

from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Sketches.SketchPrimitive import ReadPrimitive
from interchange.enums.EnumGeometry import GeometryKind
from interchange.geometry.models.GeometryCurves import ArcGeometry
from interchange.geometry.models.VectorPlane import PlaneVector
from tests.convert.formats.FusionHistoryTests import NativeRef
from tests.convert.formats.FusionParamTests import NativeText


# opposite native normals must yield the same increasing neutral angle convention
def TestArcBranches() -> None:
    for Normal, Expected in ((1.0, (Pi / 2, Pi)), (-1.0, (0.0, Pi / 2))):
        DataValue, Record, Points = MakeArc(Normal)
        Entity = ReadPrimitive(DataValue, Record, Points)
        Geometry = Entity.geometry
        assert Entity.kind == GeometryKind.KArcGeometry
        assert isinstance(Geometry, ArcGeometry)
        assert Geometry.center == Points[11]
        assert Geometry.radius == 20.0
        assert (Geometry.start_angle, Geometry.end_angle) == Approx(Expected)
        assert Entity.attributes["fusion.arc_native_clockwise"] is (Normal < 0.0)
        assert Entity.attributes["fusion.arc_native_point_ids"] == (11, 12, 13)
        assert Entity.attributes["fusion.arc_native_angles_radians"] == (0.0, Pi / 2)
        assert Entity.fixed and Entity.construction


# geometry cannot substitute for a missing or mismatched owned endpoint
def TestArcEvidence() -> None:
    DataValue, Record, Points = MakeArc(1.0)
    EndPoint = Points.pop(13)
    with Raises(ValueError, match="same-sketch"):
        ReadPrimitive(DataValue, Record, Points)
    Points[13] = PlaneVector(EndPoint.x + 0.1, EndPoint.y)
    with Raises(ValueError, match="endpoint reference disagrees"):
        ReadPrimitive(DataValue, Record, Points)


# synthetic circular records exercise the native frame without vendor payloads
def MakeArc(
    Normal: float,
) -> tuple[bytes, RecordSpan, dict[int, PlaneVector]]:
    Attributes = (
        b"\0\1"
        + Pack("<I", 3)
        + b"".join(
            NativeText(Label, False)
            + NativeText("IntrinsicMetaTypeuint64", False)
            + Pack("<Q", Value)
            for Label, Value in (
                ("EntityGenesis", 2),
                ("crv_primary_id", 8),
                ("crv_secondary_id", 0),
            )
        )
    )
    BodyValue = bytearray(182)
    BodyValue[:96] = Pack(
        "<12d", 1.0, 2.0, 0.0, 0.0, 0.0, Normal, 0.0, 1.0, 0.0, 2.0, 0.0, Pi / 2
    )
    BodyValue[96:129] = NativeRef(11) + NativeRef(13) + NativeRef(12)
    BodyValue[-51:-47] = Pack("<I", 1)
    BodyValue[-46:-42] = Pack("<I", 1)
    Payload = Attributes + BodyValue
    Record = RecordSpan(
        0, 0, len(Payload), 20, 256, "F0130424-8B7E-4092-93C9-1CA807482534", "", True
    )
    Points = {
        11: PlaneVector(10.0, 20.0),
        12: PlaneVector(10.0, 40.0),
        13: PlaneVector(10.0 - 20.0 * Normal, 20.0),
    }
    return Payload, Record, Points
