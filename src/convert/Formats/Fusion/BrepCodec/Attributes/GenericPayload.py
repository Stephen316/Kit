from convert.Formats.Fusion.BrepCodec.Attributes.GenericPrefix import MakeTagPrefix
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.Formats.Fusion.GeometryCodec.CountedText import CountedText
from convert.Formats.Fusion.GeometryCodec.GeometryValue import KGeometryValue


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
