from dataclasses import replace as Replace
from math import isclose as IsClose

from convert.formats.Fusion.Extrudes.ExtrudeRead import ReadExtrude
from convert.formats.Fusion.Extrudes.ExtParamLinks import BindExtParams
from convert.formats.Fusion.ParamProjection import ParamOrigin
from convert.formats.Fusion.RecordSpan import RecordSpan
from interchange.core.Common import FreezeMapping
from interchange.enums.EnumFeatures import BooleanOp
from interchange.features.DistanceValues import GetDistValues
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.geometry.models.VectorSpace import SpaceVector
from interchange.records.RecordParameter import Parameter


# editable extrusions retain the verified profile and component direction with live parameter links
def AttachDistExt(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    StepValue: FeatureStep,
    FrameValue: SupportPlane | None,
    Params: dict[str, Parameter],
    Authoring: tuple[SpaceVector, tuple[int, ...]] | None = None,
) -> FeatureStep:
    Origin = StepValue.provenance
    ProfileId = StepValue.attributes.get("fusion.profile_descriptor_id")
    if Origin is None or FrameValue is None or type(ProfileId) is not int:
        raise ValueError("Missing verified Fusion Extrude profile and frame")
    FeatureId = int(Origin.native_id)
    Native = ReadExtrude(BulkData, Owners, FeatureId)
    if Native.ProfileId != ProfileId:
        raise ValueError("Fusion Extrude profile proxy and projected profile disagree")
    Normal = FrameValue.transform.z_axis
    Expected = Normal if Authoring is None else Authoring[0]
    if any(
        not IsClose(Actual, Coordinate, abs_tol=1e-9, rel_tol=0.0)
        for Actual, Coordinate in zip(
            Native.Direction, (Expected.x, Expected.y, Expected.z)
        )
    ):
        raise ValueError(
            "Fusion Extrude direction is outside its verified component frame"
        )
    Links = BindExtParams(StepValue, FeatureId, Native, Params)
    LocalAxis = (
        Native.Direction if Authoring is None else (Normal.x, Normal.y, Normal.z)
    )
    Definition = DistanceExtrude(
        AlongParameterId=Links[Native.AlongId],
        Direction=SpaceVector(*LocalAxis),
        SideMode=Native.SideMode,
        AgainstParameterId=(
            Links.get(Native.AgainstId) if Native.AgainstId is not None else None
        ),
        StartOffsetId=Links.get(Native.StartId) if Native.StartId is not None else None,
        TaperParameterId=(
            Links.get(Native.TaperId) if Native.TaperId is not None else None
        ),
        SecondTaperId=(
            Links.get(Native.SecondTaperId)
            if Native.SecondTaperId is not None
            else None
        ),
    )
    Updated = Replace(
        StepValue,
        operation=BooleanOp.KCreate,
        definition=Definition,
        provenance=Replace(
            Origin, spans=Origin.spans + ParamOrigin(Owners[Native.ProxyId]).spans
        ),
        attributes=(
            StepValue.attributes
            if Authoring is None
            else FreezeMapping(
                {
                    **StepValue.attributes,
                    "fusion.extrude.authoring_occurrences": Authoring[1],
                    "fusion.extrude.native_direction": Native.Direction,
                }
            )
        ),
    )
    _ = GetDistValues(Updated, Definition, Params)
    return Updated
