from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.Sketches.FaceSupport.FaceOwner import ReadFaceDeps
from convert.Formats.Fusion.Sketches.FaceSupport.FaceRecipePick import FaceRecipePick
from convert.Formats.Fusion.Sketches.Projections.CapOutputs import (
    CapOutput,
    ReadCapOutputs,
)
from convert.Formats.Fusion.Sketches.Projections.ProjController import ReadProjCtrl


# automatic projection must consume the very same face proxy as the checked support
def ReadCapRim(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    SketchId: int,
    Recipe: FaceRecipePick,
) -> tuple[int, int, tuple[CapOutput, ...]]:
    FacePick = Recipe.SelectionValue
    BodyId = FacePick.query.get("native_body_id")
    if type(BodyId) is not int:
        raise ValueError("Fusion cap projection lacks its supported body")
    FeatureId, Roster = ReadFaceDeps(BulkData, Owners, SketchId, BodyId)
    ProxyId, DescriptorId, ControllerId = Roster[2:5]
    if ProxyId != FacePick.attributes.get(
        "fusion.proxy_object_id"
    ) or DescriptorId != FacePick.attributes.get("fusion.descriptor_object_id"):
        raise ValueError("Fusion cap boundary source and support selector disagree")
    EntryId = ReadProjCtrl(BulkData, Owners, ControllerId, FeatureId, ProxyId, 1)
    return ControllerId, EntryId, ReadCapOutputs(BulkData, Owners, EntryId)
