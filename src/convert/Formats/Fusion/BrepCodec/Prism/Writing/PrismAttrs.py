from convert.Formats.Fusion.BrepCodec.Attributes.BodyAttribute import MakeBodyTag
from convert.Formats.Fusion.BrepCodec.Attributes.FeatureAttribute import MakeFeatureTag
from convert.Formats.Fusion.BrepCodec.Attributes.SketchAttribute import MakeSketchTag
from convert.Formats.Fusion.BrepCodec.Attributes.TimestampAttribute import MakeTimestamp
from convert.Formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismTags import PrismTags
from convert.Formats.Fusion.BrepCodec.Prism.PrismLayout import (
    KBodyGeneric,
    KFirstAttribute,
    KSketchOwners,
)
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.Prism.PrismLayout import KFirstFace


# the prism attributes contract needs a shared interpretation so profile topology remains connected to its extrusion history
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
