from convert.Formats.Fusion.Extrudes.Cut.CheckCutDepsMut import CheckCutDepsMut
from convert.Formats.Fusion.Extrudes.Cut.CutDirection import CutDirection
from convert.Formats.Fusion.Extrudes.Cut.KeepCutEndPick import KeepCutEndPick
from convert.Formats.Fusion.Extrudes.Cut.ReadCutCtrlMut import ReadCutCtrlMut
from convert.Formats.Fusion.Extrudes.Cut.ReadCutDepth import ReadCutDepth
from convert.Formats.Fusion.Extrudes.Cut.ReadCutEndPick import ReadCutEndPick
from convert.Formats.Fusion.Extrudes.Cut.RetainCutEnd import RetainCutEnd
from convert.Formats.Fusion.Extrudes.ExtCacheOwner import CheckExtCache
from convert.Formats.Fusion.Extrudes.ExtrudeBinding import CheckExtBinding
from convert.Formats.Fusion.Extrudes.ExtrudeProfile import ReadExtProfile
from convert.Formats.Fusion.Extrudes.ExtrudeRead import KExtrudeGuid
from convert.Formats.Fusion.ParamProjection import ParamOrigin, ParamQuantity
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.SelectionProxy import SelectCursor
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Selection import Selection
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.Records.RecordParameter import Parameter


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
    Evidence: tuple[int, ...] = (
        ProfileProxy,
        ProfileId,
        Fields.TaperId,
        Fields.CacheId,
    )
    if Fields.AlongId is not None:
        Evidence += (Fields.AlongId,)
    Spans = tuple(ParamOrigin(Owners[Identity]).spans[0] for Identity in Evidence)
    Updated = RetainCutEnd(
        StepValue, Origin, Fields, Definition, DepthId, PickValue, Spans
    )
    return Updated, PickValue
