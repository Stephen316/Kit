from dataclasses import replace as Replace

from convert.Formats.Fusion.BrepCodec.Attributes.FlipDirection import FlipDirection

from convert.Formats.Fusion.BrepCodec.Attributes.FeatureAttribute import MakeFeatureTag
from convert.Formats.Fusion.BrepCodec.Attributes.SketchAttribute import MakeSketchTag
from convert.Formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


# the snapshot tags operation needs a consistent construction rule so native topology can resolve its owning modeling operation
def MakeSnapTags(TagSet: TopologyTags) -> tuple[GeometryRecord, ...]:
    EdgeLink = Replace(TagSet.Sketch, Direction=FlipDirection(TagSet.Sketch.Direction))
    return (
        MakeFeatureTag(6, TagSet.SideFace),
        MakeFeatureTag(7, TagSet.TopFace),
        MakeFeatureTag(8, TagSet.BottomFace),
        MakeFeatureTag(17, TagSet.TopEdge),
        MakeFeatureTag(18, TagSet.BottomEdge),
        MakeSketchTag(14, TagSet.Sketch),
        MakeSketchTag(16, TagSet.Sketch),
        MakeSketchTag(32, TagSet.Sketch),
        MakeSketchTag(33, EdgeLink),
        MakeSketchTag(42, TagSet.Sketch),
        MakeSketchTag(43, EdgeLink),
    )
