from convert.formats.Fusion.GeometryCodec.CountedText import CountedText
from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord
from convert.formats.Fusion.GeometryCodec.Prism.PrismLayout import (
    KEdgeCorners,
    KFirstCoedge,
    KFirstCurve,
    KFirstVertex,
)
from convert.formats.Fusion.GeometryCodec.Prism.PrismUse import PrismUse


def BuildEdges(UseValues: tuple[PrismUse, ...]) -> tuple[GeometryRecord, ...]:
    Owners = {
        Value.EdgeIndex: KFirstCoedge + Index for Index, Value in enumerate(UseValues)
    }
    return tuple(
        MakeRecord(
            "edge",
            (
                EntityRef(KFirstVertex + Start),
                0.0,
                EntityRef(KFirstVertex + Finish),
                1.0,
                EntityRef(Owners[Index]),
                EntityRef(KFirstCurve + Index),
                KeywordToken("forward"),
                CountedText("unknown"),
            ),
        )
        for Index, (Start, Finish) in enumerate(KEdgeCorners)
    )
