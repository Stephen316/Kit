from convert.formats.Fusion.BrepCodec.Attributes.GenericPayload import MakeTagPayload
from convert.formats.Fusion.BrepCodec.Attributes.MakeAttribute import MakeAttribute
from convert.formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


def MakeBodyTag(Owner: int, Identity: BodyIdentity, PriorLink: int) -> GeometryRecord:
    TagValue = FeatureTag(str(Identity.OperationId), (), Identity.SecondaryId)
    Payload = MakeTagPayload(TagValue)
    return MakeAttribute(Owner, "generic_tag_attrib_def", Payload, PriorLink=PriorLink)
