from convert.formats.Fusion.Extrudes.Cut.CheckCutDepsMut import CheckCutDepsMut
from convert.formats.Fusion.Extrudes.Cut.CutDirection import CutDirection
from convert.formats.Fusion.Extrudes.Cut.KeepCutEndPick import KeepCutEndPick
from convert.formats.Fusion.Extrudes.Cut.ReadCutCtrlMut import ReadCutCtrlMut
from convert.formats.Fusion.Extrudes.Cut.ReadCutDepth import ReadCutDepth
from convert.formats.Fusion.Extrudes.Cut.ReadCutEndPick import ReadCutEndPick
from convert.formats.Fusion.Extrudes.Cut.RetainCutEnd import RetainCutEnd
from convert.formats.Fusion.Extrudes.ExtCacheOwner import CheckExtCache
from convert.formats.Fusion.Extrudes.ExtrudeBinding import CheckExtBinding
from convert.formats.Fusion.Extrudes.ExtrudeProfile import ReadExtProfile
from convert.formats.Fusion.Extrudes.ExtrudeRead import KExtrudeGuid
from convert.formats.Fusion.ParamProjection import ParamOrigin, ParamQuantity
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor
from interchange.features.FeatureExtrude import ExtrudeFeature
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.records.RecordParameter import Parameter


# only a consistent end descriptor can attach a typed cut to the accepted historical target
def AttachCutEnd(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    StepValue: FeatureStep,
    Params: dict[str, Parameter],
    Frame: SupportPlane,
    Target: Selection,
) -> tuple[FeatureStep, Selection | None]:
    Origin = StepValue.provenance
    if Origin is None or Target.query.get(
        "native_component_id"
    ) != Frame.attributes.get("fusion.component_object_id"):
        raise ValueError("Fusion Cut target and sketch frame are outside one scope")
    FeatureId = int(Origin.native_id)
    Cursor = SelectCursor(BulkData, Owners, FeatureId, KExtrudeGuid)
    Fields = ReadCutCtrlMut(Cursor)
    ProfileId, ProfileProxy = ReadExtProfile(
        BulkData, Owners, Cursor, FeatureId, "one_sided"
    )
    if ProfileId != StepValue.attributes.get(
        "fusion.profile_descriptor_id"
    ) or ProfileProxy != StepValue.attributes.get("fusion.profile_selection_proxy_id"):
        raise ValueError("Fusion Cut end and projected profile references disagree")
    CheckExtCache(BulkData, Owners, FeatureId, Fields.CacheId)
    Taper = CheckExtBinding(BulkData, Owners, FeatureId, Fields.TaperId, "TaperAngle")
    if ParamQuantity(Taper).unit != "rad" or Taper.Number != 0.0:
        raise ValueError("Unsupported Fusion Cut taper")
    Depth, DepthId = ReadCutDepth(
        BulkData, Owners, StepValue, FeatureId, Params, Fields.AlongId
    )
    PickValue = None
    EndDescriptor = None
    if Fields.EndProxy is not None:
        NativePick = ReadCutEndPick(
            BulkData, Owners, FeatureId, Fields.EndProxy, Target
        )
        EndDescriptor = NativePick.DescriptorId
        PickValue = KeepCutEndPick(Owners, Target, NativePick, Fields.EndProxy)
    CheckCutDepsMut(Cursor, Fields, Target, ProfileId, ProfileProxy, EndDescriptor)
    Definition = ExtrudeFeature(
        length=Depth,
        end_condition=Fields.EndValue,
        direction=CutDirection(Fields, Frame),
    )
    Evidence = (ProfileProxy, ProfileId, Fields.TaperId, Fields.CacheId)
    if Fields.AlongId is not None:
        Evidence += (Fields.AlongId,)
    Spans = tuple(ParamOrigin(Owners[Identity]).spans[0] for Identity in Evidence)
    Updated = RetainCutEnd(
        StepValue, Origin, Fields, Definition, DepthId, PickValue, Spans
    )
    return Updated, PickValue
