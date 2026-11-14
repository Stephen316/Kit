from convert.formats.Fusion.BrepCodec.Attributes.GenericPayload import MakeTagPayload
from convert.formats.Fusion.BrepCodec.Attributes.MakeAttribute import MakeAttribute
from convert.formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


def MakeFeatureTag(Owner: int, TagValue: FeatureTag) -> GeometryRecord:
    Payload = MakeTagPayload(TagValue)
    return MakeAttribute(Owner, "generic_tag_attrib_def", Payload)
