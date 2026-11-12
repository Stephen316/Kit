from dataclasses import replace as Replace
from struct import pack as PackData

from pytest import raises as Raises

from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Revolves.RevSolidScope import FindRevCreators
from convert.formats.Fusion.Topology.BodyAnchor import KBodyGuid
from convert.formats.Fusion.Topology.BodyCollection import (
    KBodyCollection,
    KBodyComponent,
    ReadBodyList,
)
from interchange.core.Common import FreezeMapping
from interchange.enums.EnumFeatures import FeatureKind
from interchange.features.FeatureStep import FeatureStep
from tests.convert.formats.FusionHistoryTests import NativeRef


# repeated body collection entries establish the exact inventory without native geometry
def TestBodyList() -> None:
    Owners: dict[int, RecordSpan] = {}
    BulkData = bytearray()
    Members = NativeRef(10) + NativeRef(11)
    for Identity, ClassGuid, Payload in (
        (10, KBodyGuid, NativeRef(12)),
        (11, KBodyGuid, NativeRef(12)),
        (
            12,
            KBodyCollection,
            bytes(7)
            + PackData("<I", 2)
            + Members
            + bytes(8)
            + PackData("<I", 2)
            + Members
            + NativeRef(13),
        ),
        (13, KBodyComponent, bytes(2)),
    ):
        Offset = len(BulkData)
        BulkData.extend(bytes(4) + Payload)
        Owners[Identity] = RecordSpan(
            Offset, Offset, len(BulkData), Identity, 256, ClassGuid, "", True
        )
    assert ReadBodyList(bytes(BulkData), Owners, 12) == ((10, 11), 13)
    Repeated = Owners[12].EndOffset - 33
    BulkData[Repeated : Repeated + 11] = NativeRef(11)
    with Raises(ValueError, match="repeated membership disagrees"):
        _ = ReadBodyList(bytes(BulkData), Owners, 12)


# multiple independent creators are safe while an unverified modifying operation blocks publication
def TestBodySources() -> None:
    Attrs = {
        "fusion.revolve.operation": "new_body",
        "fusion.revolve.solid": True,
        "fusion.revolve.project_axis": False,
        "fusion.state_known": True,
        "fusion.rolled_back": False,
    }
    First = FeatureStep(
        "first", "First", FeatureKind.KRevolution, 0, attributes=FreezeMapping(Attrs)
    )
    Second = Replace(First, id="second", name="Second", order=1)
    assert FindRevCreators((First, Second)) == (First, Second)
    Modifying = Replace(
        Second, attributes=FreezeMapping({**Attrs, "fusion.revolve.operation": "cut"})
    )
    with Raises(ValueError, match="outside independent solid Revolves"):
        _ = FindRevCreators((First, Modifying))
    with Raises(ValueError, match="inactive or unverified"):
        _ = FindRevCreators((First, Replace(Second, suppressed=True)))
