from convert.Formats.Fusion.BrepCodec.Attributes.GenericPayload import MakeTagPayload
from convert.Formats.Fusion.BrepCodec.Attributes.MakeAttribute import MakeAttribute
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


# the feature tag operation needs a consistent construction rule so native topology can resolve its owning modeling operation
def MakeFeatureTag(Owner: int, TagValue: FeatureTag) -> GeometryRecord:
    Payload = MakeTagPayload(TagValue)
    return MakeAttribute(Owner, "generic_tag_attrib_def", Payload)
