from convert.formats.Fusion.BrepCodec.Attributes.BodyAttribute import MakeBodyTag
from convert.formats.Fusion.BrepCodec.Attributes.FeatureAttribute import MakeFeatureTag
from convert.formats.Fusion.BrepCodec.Attributes.SketchAttribute import MakeSketchTag
from convert.formats.Fusion.BrepCodec.Attributes.TimestampAttribute import MakeTimestamp
from convert.formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismTags import PrismTags
from convert.formats.Fusion.BrepCodec.Prism.PrismLayout import (
    KBodyGeneric,
    KFirstAttribute,
    KSketchOwners,
)
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.Prism.PrismLayout import KFirstFace


def PrismAttrs(Identity: BodyIdentity, TagSet: PrismTags) -> tuple[GeometryRecord, ...]:
    return (
        MakeTimestamp(1, Identity.AuthoredMicros, KBodyGeneric),
        MakeBodyTag(1, Identity, KFirstAttribute),
        *(
            MakeFeatureTag(KFirstFace + Index, Value)
            for Index, Value in enumerate(TagSet.Faces)
        ),
        *(
            MakeSketchTag(Owner, Sketch)
            for Owners, Sketch in zip(KSketchOwners, TagSet.Sketches, strict=True)
            for Owner in Owners
        ),
    )
