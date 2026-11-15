from convert.formats.Fusion.BrepCodec.Attributes.GenericPrefix import MakeTagPrefix
from convert.formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.formats.Fusion.GeometryCodec.CountedText import CountedText
from convert.formats.Fusion.GeometryCodec.GeometryValue import KGeometryValue


# feature identity must survive serialization so native history references resolve to the intended modeling operation
def MakeTagPayload(Value: FeatureTag) -> tuple[KGeometryValue, ...]:
    return (
        *MakeTagPrefix(),
        len(Value.PrimaryId.encode("ascii")),
        CountedText(Value.PrimaryId),
        Value.SecondaryId,
        len(Value.OperationIds),
        *Value.OperationIds,
        Value.ApproachId,
    )
