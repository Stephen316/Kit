from convert.Formats.Fusion.GeometryCodec.CountedText import CountedText
from convert.Formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.Formats.Fusion.GeometryCodec.MakeRecord import MakeRecord
from convert.Formats.Fusion.GeometryCodec.Prism.PrismLayout import (
    KEdgeCorners,
    KFirstCoedge,
    KFirstCurve,
    KFirstVertex,
)
from convert.Formats.Fusion.GeometryCodec.Prism.PrismUse import PrismUse


# the edges operation needs a consistent construction rule so geometric values retain their native record boundaries
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
