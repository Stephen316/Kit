from dataclasses import replace as Replace

from convert.Formats.Fusion.Extrudes.ExtParamLinks import BindExtRoles
from convert.Formats.Fusion.Extrudes.Plane.NativePlaneExt import NativePlaneExt
from convert.Formats.Fusion.ParamProjection import ParamOrigin
from convert.Formats.Fusion.RecordSpan import RecordSpan
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumFeatures import BooleanOp
from interchange.Features.FeaturePlaneExt import PlaneExtrude
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Selection import SelectPathElem, Selection
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordParameter import Parameter


# the selected plane remains a typed feature input with its owned offset and distance
def AttachPlaneExt(
    StepValue: FeatureStep,
    FeatureId: int,
    Native: NativePlaneExt,
    PlaneValue: SupportPlane,
    PlaneStep: FeatureStep,
    Params: dict[str, Parameter],
    Owners: dict[int, RecordSpan],
) -> tuple[FeatureStep, Selection]:
    Origin = StepValue.provenance
    if (
        Origin is None
        or StepValue.attributes.get("fusion.profile_descriptor_id") != Native.ProfileId
    ):
        raise ValueError("Fusion plane Extrude requires the verified profile selection")
    Bound = BindExtRoles(
        StepValue,
        FeatureId,
        Params,
        (
            (
                Native.OffsetId,
                "ProfileOffset" if Native.Role == "start" else "Side1Offset",
                "cm",
            ),
            (Native.AlongId, "AlongDistance", "cm"),
            (Native.TaperId, "TaperAngle", "rad"),
        ),
    )
    Evidence = ParamOrigin(Owners[Native.ProxyId])
    PickValue = Selection(
        id=f"fusion-selection-{Native.ProxyId}-plane-{Native.Role}",
        name=f"{Native.Role} plane",
        path=(SelectPathElem("support_plane", PlaneValue.id),),
        provenance=Replace(
            Evidence,
            spans=Evidence.spans
            + tuple(
                SpanValue
                for Identity in dict.fromkeys(Native.EvidenceIds)
                if Identity != Native.ProxyId
                for SpanValue in ParamOrigin(Owners[Identity]).spans
            ),
        ),
    )
    Definition = PlaneExtrude(
        PlaneSelectionId=PickValue.id,
        Direction=SpaceVector(*Native.Direction),
        LimitRole=Native.Role,
        OffsetParameterId=Bound[Native.OffsetId],
        LengthParameterId=None if Native.AlongId is None else Bound[Native.AlongId],
        TaperParameterId=None if Native.TaperId is None else Bound[Native.TaperId],
    )
    ProfileOrigin = ParamOrigin(Owners[Native.ProfileProxyId])
    return (
        Replace(
            StepValue,
            operation=BooleanOp.KCreate,
            definition=Definition,
            input_feature_ids=tuple(
                dict.fromkeys((*StepValue.input_feature_ids, PlaneStep.id))
            ),
            selection_ids=(*StepValue.selection_ids, PickValue.id),
            provenance=Replace(Origin, spans=Origin.spans + ProfileOrigin.spans),
            attributes=FreezeMapping(
                {
                    **StepValue.attributes,
                    "fusion.extrude.result_offset": Native.ResultOffset,
                }
            ),
        ),
        PickValue,
    )
