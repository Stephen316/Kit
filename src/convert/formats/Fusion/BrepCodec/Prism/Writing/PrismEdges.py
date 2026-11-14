from convert.formats.Fusion.BrepCodec.Prism.Models.PrismFrame import PrismFrame
from convert.formats.Fusion.GeometryCodec.CountedText import CountedText
from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord
from convert.formats.Fusion.GeometryCodec.Prism.BuildUses import BuildUses
from convert.formats.Fusion.GeometryCodec.Prism.PrismLayout import (
    KFirstCoedge,
    KFirstCurve,
    KFirstVertex,
)


def PrismEdges(Frame: PrismFrame) -> tuple[GeometryRecord, ...]:
    Owners = {
        (Value.EdgeIndex, Value.FaceIndex): KFirstCoedge + Index
        for Index, Value in enumerate(BuildUses())
    }
    return tuple(
        MakeRecord(
            "edge",
            (
                EntityRef(KFirstVertex + Value.StartCorner),
                Value.LowerParam,
                EntityRef(KFirstVertex + Value.EndCorner),
                Value.UpperParam,
                EntityRef(Owners[(Index, Value.OwnerFace)]),
                EntityRef(KFirstCurve + Index),
                KeywordToken("forward"),
                CountedText("unknown"),
            ),
        )
        for Index, Value in enumerate(Frame.Edges)
    )
