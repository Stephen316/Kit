# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from struct import pack as PackData

from pytest import raises as Raises

from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Sketches.SketchFrame import ReadFrame
from convert.formats.Fusion.Sketches.SketchPrimitive import ReadPrimitive
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.VectorPlane import PlaneVector
from tests.convert.formats.FusionHistoryTests import NativeRef
from tests.convert.formats.FusionParamTests import NativeText


# explicit component frames need a validated third axis and scaled origin
def TestSketchFrame() -> None:
    Matrix = (
        0.0,
        -1.0,
        0.0,
        1.0,
        1.0,
        0.0,
        0.0,
        2.0,
        0.0,
        0.0,
        1.0,
        3.0,
        0.0,
        0.0,
        0.0,
        1.0,
    )
    BodyValue = bytes(3) + PackData("<16d", *Matrix) + bytes(1) + NativeRef(20)
    Frame, Component = ReadFrame(BodyValue)
    assert Component == 20
    assert (Frame.origin.x, Frame.origin.y, Frame.origin.z) == (10.0, 20.0, 30.0)
    assert Frame.x_axis.y == 1.0 and Frame.y_axis.x == -1.0
    Modified = bytearray(BodyValue)
    Modified[3 + 8 * 10 : 3 + 8 * 11] = PackData("<d", -1.0)
    with Raises(ValueError, match="normal disagrees"):
        _ = ReadFrame(bytes(Modified))


# line caches must agree with the same sketch endpoint records
def TestSketchLine() -> None:
    Attributes = (
        b"\0\1"
        + PackData("<I", 3)
        + b"".join(
            NativeText(Label, False)
            + NativeText("IntrinsicMetaTypeuint64", False)
            + PackData("<Q", Value)
            for Label, Value in (
                ("EntityGenesis", 2),
                ("crv_primary_id", 8),
                ("crv_secondary_id", 0),
            )
        )
    )
    BodyValue = bytearray(171)
    BodyValue[:48] = PackData("<6d", 0.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    BodyValue[96:118] = NativeRef(12) + NativeRef(11)
    Payload = Attributes + BodyValue
    SpanValue = RecordSpan(
        0, 0, len(Payload), 13, 256, "DCA267ED-D615-4934-B64F-AD805E8003E2", "", True
    )
    Start = PlaneVector(0.0, 0.0)
    EndValue = PlaneVector(10.0, 0.0)
    Entity = ReadPrimitive(Payload, SpanValue, {11: Start, 12: EndValue})
    assert Entity.geometry == LineGeometry(Start, EndValue)
    with Raises(ValueError, match="endpoint cache disagrees"):
        _ = ReadPrimitive(Payload, SpanValue, {11: Start, 12: PlaneVector(20.0, 0.0)})
