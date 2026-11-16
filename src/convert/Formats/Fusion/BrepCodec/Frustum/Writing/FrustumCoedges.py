from dataclasses import replace as Replace

from convert.Formats.Fusion.BrepCodec.Frustum.Models.FrustumFrame import FrustumFrame
from convert.Formats.Fusion.GeometryCodec.CylinderCoedges import BuildCoedges
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


# the frustum coedges contract needs a shared interpretation so circular boundaries retain consistent cone and rim geometry
def FrustumCoedges(Frame: FrustumFrame) -> tuple[GeometryRecord, ...]:
    Senses = (
        Frame.Upper.SideReverse,
        Frame.Lower.SideReverse,
        Frame.Upper.CapReverse,
        Frame.Lower.CapReverse,
    )
    return tuple(
        Replace(Record, Fields=(*Record.Fields[:7], Reverse, *Record.Fields[8:]))
        for Record, Reverse in zip(BuildCoedges(), Senses, strict=True)
    )
