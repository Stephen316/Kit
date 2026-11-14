from dataclasses import replace as Replace

from convert.formats.Fusion.BrepCodec.Models.VertexIndices import VertexIndices
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


def ApplyVertices(
    Records: tuple[GeometryRecord, ...], Vertices: VertexIndices
) -> tuple[GeometryRecord, ...]:
    Results = list(Records)
    for Ordinal, EdgeIndex in ((20, Vertices.TopIndex), (21, Vertices.BottomIndex)):
        Current = Results[Ordinal]
        Results[Ordinal] = Replace(
            Current,
            Fields=(*Current.Fields[:4], EdgeIndex, *Current.Fields[5:]),
        )
    return tuple(Results)
