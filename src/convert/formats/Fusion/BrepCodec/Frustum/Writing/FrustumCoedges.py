from dataclasses import replace as Replace

from convert.formats.Fusion.BrepCodec.Frustum.Models.FrustumFrame import FrustumFrame
from convert.formats.Fusion.GeometryCodec.CylinderCoedges import BuildCoedges
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


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
