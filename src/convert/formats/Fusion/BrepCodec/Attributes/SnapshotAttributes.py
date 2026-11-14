from dataclasses import replace as Replace

from convert.formats.Fusion.BrepCodec.Attributes.FlipDirection import FlipDirection

from convert.formats.Fusion.BrepCodec.Attributes.FeatureAttribute import MakeFeatureTag
from convert.formats.Fusion.BrepCodec.Attributes.SketchAttribute import MakeSketchTag
from convert.formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


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
