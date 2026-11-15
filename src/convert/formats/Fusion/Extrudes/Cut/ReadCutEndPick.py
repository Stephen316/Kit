from convert.formats.Fusion.BodyInputs.ProxyInputCheck import CheckInputProxy
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import ReadSelectList
from convert.formats.Fusion.Topology.BodyPick import (
    KCutPickMarker,
    BodyPick,
    ReadBodyPick,
)
from interchange.geometry.models.Selection import Selection


# the extent proxy and descriptor carry different modes from the accepted target
def ReadCutEndPick(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    FeatureId: int,
    ProxyId: int,
    Target: Selection,
) -> BodyPick:
    Descriptors, Attributes = ReadSelectList(BulkData, Owners, ProxyId, FeatureId)
    if len(Descriptors) != 1 or Attributes:
        raise ValueError("Fusion Cut requires one distinct extent field descriptor")
    (DescriptorId,) = Descriptors
    if ProxyId == Target.attributes.get(
        "fusion.proxy_object_id"
    ) or DescriptorId == Target.attributes.get("fusion.descriptor_object_id"):
        raise ValueError("Fusion Cut extent and target roles reuse a selector")
    CheckInputProxy(BulkData, Owners, ProxyId, Descriptors, 5, Marker=KCutPickMarker)
    PickValue = ReadBodyPick(BulkData, Owners, DescriptorId, FeatureId, CutEnding=True)
    if (
        PickValue.BodyId != Target.query.get("native_body_id")
        or PickValue.AnchorId != Target.query.get("native_anchor_id")
        or PickValue.SourceId != Target.query.get("native_source_id")
        or PickValue.AnchorGuid != Target.attributes.get("fusion.anchor_guid")
    ):
        raise ValueError("Fusion Cut extent and target historical body routes disagree")
    return PickValue
