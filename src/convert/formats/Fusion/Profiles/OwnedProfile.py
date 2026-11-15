from convert.formats.Fusion.Extrudes.ExtrudeRead import KExtrudeGuid
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.ParamProjection import ParamOrigin as RecordOrigin
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import (
    KSelectProxy,
    ReadSelectIds,
    SelectCursor,
)
from interchange.records.RecordProvenance import ProvenanceSpan

# the three observed controls place the profile pair in different slots of the dependency list
KProfileLayouts = {
    (426, 4, 2): (5, 0),
    (446, 2, 2): (7, 2),
    (467, 2, 1): (8, 2),
}


# the feature selection must agree with the descriptor before a contour can claim its ownership
def ReadOwnedPick(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    FeatureId: int,
    DescriptorId: int,
) -> tuple[tuple[ProvenanceSpan, ...], dict[str, int]]:
    Feature = Owners.get(FeatureId)
    if Feature is None or Feature.ClassGuid != KExtrudeGuid:
        return (), {}
    Payload = BulkData[Feature.PayloadOffset + 4 : Feature.EndOffset]
    if len(Payload) not in (426, 446, 467) or Payload[:9] != b"\0\1" + bytes(7):
        return (), {}
    Cursor = MetaCursor(Payload)
    Cursor.Offset = 9
    Operation, SideMode, Extent = (Cursor.ReadWord() for _ in range(3))
    Layout = KProfileLayouts.get((len(Payload), Operation, Extent))
    if Layout is None or SideMode != 1 or Cursor.TakeBytes(6) != b"\0\1" + bytes(4):
        return (), {}
    CountValue, PairOffset = Layout
    Cursor.Offset = 113
    if Cursor.TakeBytes(15) != bytes(15) or Cursor.ReadWord() != 1:
        raise ValueError("Unsupported Fusion owned profile wall or selection count")
    ProxyId = ReadNativeRef(Cursor)
    Proxy = SelectCursor(BulkData, Owners, ProxyId, KSelectProxy)
    Targets, Attributes = ReadSelectIds(BulkData, Owners, ProxyId, FeatureId, 1)
    Cursor.Offset = 249
    if (
        len(Proxy.DataValue) != 105
        or Targets != (DescriptorId,)
        or Attributes
        or Cursor.ReadWord() != CountValue
    ):
        raise ValueError("Fusion owned profile proxy and descriptor disagree")
    Dependencies = tuple(ReadNativeRef(Cursor) for _ in range(CountValue))
    if len(set(Dependencies)) != CountValue or Dependencies[
        PairOffset : PairOffset + 2
    ] != (ProxyId, DescriptorId):
        raise ValueError("Fusion owned profile dependency copies disagree")
    return RecordOrigin(Owners[ProxyId]).spans, {
        "fusion.profile_selection_proxy_id": ProxyId
    }
