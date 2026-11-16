from math import isclose as IsClose

from convert.Formats.Fusion.Extrudes.ExtrudeRead import ReadExtrude
from convert.Formats.Fusion.Extrudes.ExtParamLinks import BindExtParams
from convert.Formats.Fusion.Extrudes.RetainExtProof import RetainExtProof
from convert.Formats.Fusion.RecordSpan import RecordSpan
from interchange.Features.DistanceValues import GetDistValues
from interchange.Features.FeatureDistExt import DistanceExtrude
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordParameter import Parameter


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
    ProxyId = StepValue.attributes.get("fusion.profile_selection_proxy_id")
    if Native.ProfileId != ProfileId or (
        ProxyId is not None and ProxyId != Native.ProxyId
    ):
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
    Updated = RetainExtProof(
        StepValue,
        Definition,
        Origin,
        Native,
        Owners,
        Params[Definition.AlongParameterId],
        FrameValue.id,
        None if Authoring is None else Authoring[1],
    )
    _ = GetDistValues(Updated, Definition, Params)
    return Updated
