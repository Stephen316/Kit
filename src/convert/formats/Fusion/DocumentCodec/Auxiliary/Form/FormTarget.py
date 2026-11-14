from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.LeadGuid import LeadGuid


def FormTarget(
    Value: KEntityValue, Owners: dict[int, EntityRecord], ClassGuid: str
) -> EntityRecord:
    if not isinstance(Value, LocalRef):
        raise ValueError("Form link requires a local Design entity reference")
    Target = Owners.get(Value.ObjectId)
    if Target is None or LeadGuid(Target) != ClassGuid:
        raise ValueError("Form reference has no compatible primary entity")
    return Target
