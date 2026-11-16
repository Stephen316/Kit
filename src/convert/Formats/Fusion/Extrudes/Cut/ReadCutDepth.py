from dataclasses import replace as Replace

from convert.Formats.Fusion.Extrudes.ExtParamLinks import BindExtRoles
from convert.Formats.Fusion.Extrudes.ExtrudeBinding import CheckExtBinding
from convert.Formats.Fusion.ParamProjection import ParamQuantity
from convert.Formats.Fusion.RecordSpan import RecordSpan
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordParameter import Parameter, ParameterValue


# the neutral depth magnitude stays linked to the original signed authored parameter
def ReadCutDepth(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    StepValue: FeatureStep,
    FeatureId: int,
    Params: dict[str, Parameter],
    AlongId: int | None,
) -> tuple[ParameterValue | None, str | None]:
    if AlongId is None:
        if any(
            Value.owner_id == StepValue.id
            and Value.attributes.get("fusion.native_role") == "AlongDistance"
            for Value in Params.values()
        ):
            raise ValueError("Fusion through all Cut has an unexpected depth binding")
        return None, None
    Native = CheckExtBinding(BulkData, Owners, FeatureId, AlongId, "AlongDistance")
    Links = BindExtRoles(
        StepValue, FeatureId, Params, ((AlongId, "AlongDistance", "cm"),)
    )
    ParameterId = Links[AlongId]
    ParameterData = Params[ParameterId]
    if (
        ParameterData.value != ParamQuantity(Native)
        or not Native.Number < 0.0
        or ParameterData.expression is None
        or ParameterData.expression.source != Native.Formula
    ):
        raise ValueError("Fusion blind Cut lacks its signed distance expression")
    return Replace(ParameterData.value, value=-Native.Number), ParameterId
