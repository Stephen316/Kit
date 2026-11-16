from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismFrame import PrismFrame
from convert.Formats.Fusion.GeometryCodec.CountedText import CountedText
from convert.Formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.Formats.Fusion.GeometryCodec.MakeRecord import MakeRecord
from convert.Formats.Fusion.GeometryCodec.Prism.BuildUses import BuildUses
from convert.Formats.Fusion.GeometryCodec.Prism.PrismLayout import (
    KFirstCoedge,
    KFirstCurve,
    KFirstVertex,
)


# the prism edges contract needs a shared interpretation so profile topology remains connected to its extrusion history
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
