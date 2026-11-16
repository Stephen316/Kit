from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismFrame import PrismFrame
from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismTags import PrismTags
from convert.Formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.RegionFrame import (
    RegionFrame,
)
from convert.Formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from convert.Formats.Fusion.GeometryCodec.Prism.CuboidBody import CuboidBody


# prism snapshot needs an explicit state contract so supporting records retain their owning document relationships
@MakeDataClass(frozen=True, slots=True)
class PrismSnapshot:
    Model: CuboidBody
    TagSet: PrismTags
    Stamp: GeometryStamp
    Header: BrepHeader
    Frame: PrismFrame
    Profile: RegionFrame
    Sketch: RegionFrame
