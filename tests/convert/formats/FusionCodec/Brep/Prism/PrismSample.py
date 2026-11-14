from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag
from convert.formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.formats.Fusion.BrepCodec.Models.SketchLink import SketchLink
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismTags import PrismTags
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from convert.formats.Fusion.GeometryCodec.Prism.CuboidBody import CuboidBody


@MakeDataClass(frozen=True, slots=True)
class PrismSample:
    Model: CuboidBody
    Identity: BodyIdentity
    TagSet: PrismTags
    History: HistoryState
    Stamp: GeometryStamp


def MakePrism() -> PrismSample:
    return PrismSample(
        CuboidBody(17.0, 23.0, 31.0, (-7.0, 13.0, 5.0)),
        BodyIdentity(7, 1701, 13, 1794477991119457.0),
        PrismTags(
            tuple(
                FeatureTag(Value, (1701,)) for Value in ("1", "2", "4", "6", "3", "5")
            ),
            tuple(SketchLink(Value, 0, 0, 1, 1) for Value in range(901, 905)),
        ),
        HistoryState(17, 2, 17, 8, 2),
        GeometryStamp("Kit", "Prism history integration", "2026-11-12T00:00:00Z"),
    )
