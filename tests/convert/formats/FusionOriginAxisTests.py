from struct import pack as PackData

from pytest import raises as Raises

from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Revolves.OriginAxis import (
    KAxisGuid,
    KComponentGuid,
    KOriginGuid,
    ReadOriginAxis,
)
from interchange.geometry.models.VectorSpace import SpaceVector
from tests.convert.formats.FusionHistoryTests import NativeRef
from tests.convert.formats.FusionParamTests import NativeText


# an axis cannot supply geometry to a sketch owned by another component
def TestOriginOwner() -> None:
    BulkData, Owners = AxisFixture(40)
    assert ReadOriginAxis(BulkData, Owners, 40, 3) == (
        "Y",
        SpaceVector(0.0, 0.0, 0.0),
        SpaceVector(0.0, 1.0, 0.0),
        37,
    )
    with Raises(ValueError, match="not owned"):
        _ = ReadOriginAxis(BulkData, Owners, 40, 4)
    BulkData, Owners = AxisFixture(45)
    with Raises(ValueError, match="not owned"):
        _ = ReadOriginAxis(BulkData, Owners, 40, 3)


# synthetic reciprocal references let ownership failures vary independently of geometry
def AxisFixture(Member: int) -> tuple[bytes, dict[int, RecordSpan]]:
    AxisBody = (
        b"\0\1"
        + PackData("<I", 1)
        + NativeText("EntityGenesis", False)
        + NativeText("IntrinsicMetaTypeuint64", False)
        + PackData("<Q6d", 0, 0, 0, 0, 0, 1, 0)
        + bytes(26)
        + NativeText("Y")
        + bytes(37)
        + NativeRef(37)
    )
    Container = (
        PackData("<II", 0, 7)
        + b"".join(NativeRef(Entry) for Entry in (38, 39, Member, 41, 42, 43, 44))
        + NativeRef(3)
    )
    Owners: dict[int, RecordSpan] = {}
    BulkData = bytearray()
    for Identity, ClassGuid, BodyValue in (
        (3, KComponentGuid, b""),
        (4, KComponentGuid, b""),
        (37, KOriginGuid, Container),
        (40, KAxisGuid, AxisBody),
    ):
        Offset = len(BulkData)
        BulkData.extend(bytes(4) + BodyValue)
        Owners[Identity] = RecordSpan(
            Offset, Offset, len(BulkData), Identity, 256, ClassGuid, "", True
        )
    return bytes(BulkData), Owners
