# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import replace as Replace
from struct import pack as PackData

from pytest import raises as Raises

from convert.formats.Fusion.NativePlane import (
    KPlaneFeature,
    KPlaneObject,
    ReadNativePlane,
)
from convert.formats.Fusion.PlaneCollection import (
    KDatumCollection,
    KDatumComponent,
    ReadPlaneComp,
)
from convert.formats.Fusion.RecordSpan import RecordSpan
from tests.convert.formats.FusionHistoryTests import NativeRef
from tests.convert.formats.FusionParamTests import NativeText


# an angled component datum exercises scale conversion and reciprocal ownership
def PlaneFixture(
    OwnerId: int = 100, AxisXX: float = 0.0
) -> tuple[bytes, RecordSpan, dict[int, RecordSpan]]:
    Feature = (
        bytes(23)
        + NativeRef(101)
        + NativeText("WorkPlane")
        + PackData("<Q", 7)
        + NativeText("")
    )
    Geometry = b"".join(
        (
            bytes(4),
            b"\0\1",
            PackData("<I", 1),
            NativeText("EntityGenesis", False),
            NativeText("IntrinsicMetaTypeuint64", False),
            PackData("<QI", 0, 2),
            bytes(17),
            PackData("<9d", 1.0, -2.0, 0.5, AxisXX, 1.0, 0.0, 0.0, 0.0, 1.0),
            bytes(16),
            NativeText(""),
            NativeRef(900),
            PackData("<Q", 7),
            bytes(1),
            NativeRef(OwnerId),
            b"\0\1",
            NativeText("Angled datum"),
        )
    )
    FeatureSpan = RecordSpan(0, 0, len(Feature), 100, 256, KPlaneFeature, "", True)
    PlaneSpan = RecordSpan(
        len(Feature),
        len(Feature),
        len(Feature) + len(Geometry),
        101,
        257,
        KPlaneObject,
        "",
        True,
    )
    return Feature + Geometry, FeatureSpan, {100: FeatureSpan, 101: PlaneSpan}


# component axes and centimetre translation must preserve their distinct scales
def TestNativePlane() -> None:
    BulkData, Feature, Owners = PlaneFixture()
    PlaneValue = ReadNativePlane(BulkData, Feature, Owners)
    assert PlaneValue.id == "fusion-plane-101"
    assert PlaneValue.name == "Angled datum"
    assert PlaneValue.transform.origin.x == 10.0
    assert PlaneValue.transform.origin.y == -20.0
    assert PlaneValue.transform.origin.z == 5.0
    assert PlaneValue.transform.z_axis.x == 1.0
    assert PlaneValue.provenance is not None and len(PlaneValue.provenance.spans) == 2


# corrupt owner references or nonrigid axes must not become neutral support geometry
def TestRejectPlane() -> None:
    BulkData, Feature, Owners = PlaneFixture(OwnerId=102)
    with Raises(ValueError, match="owner or ordinal disagrees"):
        _ = ReadNativePlane(BulkData, Feature, Owners)
    BulkData, Feature, Owners = PlaneFixture(AxisXX=1.0)
    with Raises(ValueError, match="axes are not orthonormal"):
        _ = ReadNativePlane(BulkData, Feature, Owners)


# the component is usable only when both native membership copies agree
def TestPlaneScope() -> None:
    BulkData, Feature, Owners = PlaneFixture()
    BulkData += NativeRef(900)
    Owners[101] = Replace(Owners[101], EndOffset=len(BulkData))
    Offset = len(BulkData)
    BulkData += (
        bytes(6)
        + PackData("<I", 1)
        + NativeRef(101)
        + bytes(30)
        + PackData("<I", 1)
        + NativeRef(101)
        + NativeRef(800)
    )
    Owners[900] = RecordSpan(
        Offset, Offset, len(BulkData), 900, 258, KDatumCollection, "", True
    )
    Offset = len(BulkData)
    BulkData += bytes(4)
    Owners[800] = RecordSpan(
        Offset, Offset, len(BulkData), 800, 259, KDatumComponent, "", True
    )
    PlaneValue = ReadNativePlane(BulkData, Feature, Owners)
    assert ReadPlaneComp(BulkData, Owners, PlaneValue) == (800, 900)
    Repeated = Owners[900].EndOffset - 22
    BadBulk = BulkData[:Repeated] + NativeRef(102) + BulkData[Repeated + 11 :]
    with Raises(ValueError, match="membership disagrees"):
        _ = ReadPlaneComp(BadBulk, Owners, PlaneValue)
