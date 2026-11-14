from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismFrame import PrismFrame
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismTags import PrismTags
from convert.formats.Fusion.DocumentCodec.Auxiliary.PrismSnapshot.Models.RegionFrame import (
    RegionFrame,
)
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from convert.formats.Fusion.GeometryCodec.Prism.CuboidBody import CuboidBody


@MakeDataClass(frozen=True, slots=True)
class PrismSnapshot:
    Model: CuboidBody
    TagSet: PrismTags
    Stamp: GeometryStamp
    Header: BrepHeader
    Frame: PrismFrame
    Profile: RegionFrame
    Sketch: RegionFrame
