from convert.formats.Fusion.BrepCodec.Attributes.BodyAttribute import MakeBodyTag
from convert.formats.Fusion.BrepCodec.Attributes.FeatureAttribute import MakeFeatureTag
from convert.formats.Fusion.BrepCodec.Attributes.SketchAttribute import MakeSketchTag
from convert.formats.Fusion.BrepCodec.Attributes.TimestampAttribute import MakeTimestamp
from convert.formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


def MakeHistoryTags(
    Identity: BodyIdentity, TagSet: TopologyTags
) -> tuple[GeometryRecord, ...]:
    return (
        MakeTimestamp(1, Identity.AuthoredMicros, 27),
        MakeBodyTag(1, Identity, 26),
        MakeFeatureTag(4, TagSet.SideFace),
        MakeFeatureTag(5, TagSet.TopFace),
        MakeFeatureTag(6, TagSet.BottomFace),
        MakeFeatureTag(15, TagSet.TopEdge),
        MakeFeatureTag(16, TagSet.BottomEdge),
        MakeSketchTag(12, TagSet.Sketch),
        MakeSketchTag(14, TagSet.Sketch),
    )
