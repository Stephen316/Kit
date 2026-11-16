from dataclasses import replace as Replace

from convert.Formats.Fusion.BrepCodec.Frustum.Models.FrustumFrame import FrustumFrame
from convert.Formats.Fusion.GeometryCodec.CylinderEdges import BuildEdges
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


# the frustum edges contract needs a shared interpretation so circular boundaries retain consistent cone and rim geometry
def FrustumEdges(Frame: FrustumFrame) -> tuple[GeometryRecord, ...]:
    return tuple(
        Replace(
            Record,
            Fields=(
                *Record.Fields[:4],
                float(Value.EdgeStart),
                Record.Fields[5],
                float(Value.EdgeEnd),
                *Record.Fields[7:9],
                Value.EdgeReverse,
                Record.Fields[10],
            ),
        )
        for Record, Value in zip(BuildEdges(), (Frame.Upper, Frame.Lower), strict=True)
    )
