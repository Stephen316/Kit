from convert.Formats.Fusion.BrepCodec.Attributes.GenericPayload import MakeTagPayload
from convert.Formats.Fusion.BrepCodec.Attributes.MakeAttribute import MakeAttribute
from convert.Formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.Formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


# body tags need operation ownership so reconstructed history can identify the feature that produced each body
def MakeBodyTag(Owner: int, Identity: BodyIdentity, PriorLink: int) -> GeometryRecord:
    TagValue = FeatureTag(str(Identity.OperationId), (), Identity.SecondaryId)
    Payload = MakeTagPayload(TagValue)
    return MakeAttribute(Owner, "generic_tag_attrib_def", Payload, PriorLink=PriorLink)
