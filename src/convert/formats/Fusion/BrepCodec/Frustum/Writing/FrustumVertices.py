from dataclasses import replace as Replace

from convert.formats.Fusion.BrepCodec.Frustum.Models.FrustumFrame import FrustumFrame
from convert.formats.Fusion.GeometryCodec.CylinderVertices import BuildVertices
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


def FrustumVertices(Frame: FrustumFrame) -> tuple[GeometryRecord, ...]:
    return tuple(
        Replace(
            Record, Fields=(*Record.Fields[:4], Value.VertexIndex, Record.Fields[5])
        )
        for Record, Value in zip(
            BuildVertices(), (Frame.Upper, Frame.Lower), strict=True
        )
    )
