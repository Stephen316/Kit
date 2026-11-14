from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.formats.Fusion.BrepCodec.Models.TopologyTags import TopologyTags
from convert.formats.Fusion.GeometryCodec.CylinderBody import CylinderBody
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp


@MakeDataClass(frozen=True, slots=True)
class BrepSample:
    Model: CylinderBody
    Identity: BodyIdentity
    TagSet: TopologyTags
    History: HistoryState
    Stamp: GeometryStamp


def MakeSample() -> BrepSample:
    TagSet = TopologyTags(
        FeatureTag("3", (1701,)),
        FeatureTag("2", (1701,)),
        FeatureTag("1", (1701,)),
        FeatureTag("-1", (1701,)),
        FeatureTag("-901", (1701,)),
        SketchLink(901, (1 << 63) + 37, 0, 1, 1),
    )
    return BrepSample(
        CylinderBody(12.5, 21.75, (3.0, -4.0, 5.0)),
        BodyIdentity(7, 1701, 13, 1794477991119457),
        TagSet,
        HistoryState(17, 2, 17, 8, 2),
        GeometryStamp("Kit", "BRep integration", "2026-11-12T00:00:00Z"),
    )
