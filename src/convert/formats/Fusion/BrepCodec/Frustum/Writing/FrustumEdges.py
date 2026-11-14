from dataclasses import replace as Replace

from convert.formats.Fusion.BrepCodec.Frustum.Models.FrustumFrame import FrustumFrame
from convert.formats.Fusion.GeometryCodec.CylinderEdges import BuildEdges
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


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
