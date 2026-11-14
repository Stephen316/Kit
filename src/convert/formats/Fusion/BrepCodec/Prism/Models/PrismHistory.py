from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismFrame import PrismFrame
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismTags import PrismTags
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from convert.formats.Fusion.GeometryCodec.Prism.CuboidBody import CuboidBody


@MakeDataClass(frozen=True, slots=True)
class PrismHistory:
    Model: CuboidBody
    Identity: BodyIdentity
    TagSet: PrismTags
    History: HistoryState
    Stamp: GeometryStamp
    Frame: PrismFrame
    Header: BrepHeader
