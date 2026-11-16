from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Models.BodyIdentity import BodyIdentity
from convert.Formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.Formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismFrame import PrismFrame
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismTags import PrismTags
from convert.Formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from convert.Formats.Fusion.GeometryCodec.Prism.CuboidBody import CuboidBody


# prism history needs an explicit state contract so profile topology remains connected to its extrusion history
@MakeDataClass(frozen=True, slots=True)
class PrismHistory:
    Model: CuboidBody
    Identity: BodyIdentity
    TagSet: PrismTags
    History: HistoryState
    Stamp: GeometryStamp
    Frame: PrismFrame
    Header: BrepHeader
