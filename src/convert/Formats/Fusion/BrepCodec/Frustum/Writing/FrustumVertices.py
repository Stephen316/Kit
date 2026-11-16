from dataclasses import replace as Replace

from convert.Formats.Fusion.BrepCodec.Frustum.Models.FrustumFrame import FrustumFrame
from convert.Formats.Fusion.GeometryCodec.CylinderVertices import BuildVertices
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


# the frustum vertices contract needs a shared interpretation so circular boundaries retain consistent cone and rim geometry
def FrustumVertices(Frame: FrustumFrame) -> tuple[GeometryRecord, ...]:
    return tuple(
        Replace(
            Record, Fields=(*Record.Fields[:4], Value.VertexIndex, Record.Fields[5])
        )
        for Record, Value in zip(
            BuildVertices(), (Frame.Upper, Frame.Lower), strict=True
        )
    )
