from math import pi as KCircleHalf

from convert.formats.Fusion.GeometryCodec.CountedText import CountedText
from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


# the edges operation needs a consistent construction rule so geometric values retain their native record boundaries
def BuildEdges() -> tuple[GeometryRecord, ...]:
    return tuple(
        MakeRecord(
            "edge",
            (
                EntityRef(Vertex),
                -KCircleHalf,
                EntityRef(Vertex),
                KCircleHalf,
                EntityRef(Coedge),
                EntityRef(Curve),
                KeywordToken("forward"),
                CountedText("unknown"),
            ),
        )
        for Vertex, Coedge, Curve in ((20, 11, 22), (21, 12, 23))
    )
