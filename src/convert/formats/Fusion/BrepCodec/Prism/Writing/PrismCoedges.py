from convert.formats.Fusion.BrepCodec.Prism.Models.PrismFrame import PrismFrame
from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord
from convert.formats.Fusion.GeometryCodec.Prism.BuildUses import BuildUses
from convert.formats.Fusion.GeometryCodec.Prism.PrismLayout import (
    KFirstCoedge,
    KFirstEdge,
    KFirstLoop,
)


def PrismCoedges(Frame: PrismFrame) -> tuple[GeometryRecord, ...]:
    UseValues = BuildUses()
    Lookup = {
        (Value.Start, Value.Finish): KFirstCoedge + Index
        for Index, Value in enumerate(UseValues)
    }
    return tuple(
        MakeRecord(
            "coedge",
            (
                EntityRef(
                    KFirstCoedge + 4 * Value.FaceIndex + (Value.RingIndex + 1) % 4
                ),
                EntityRef(
                    KFirstCoedge + 4 * Value.FaceIndex + (Value.RingIndex - 1) % 4
                ),
                EntityRef(Lookup[(Value.Finish, Value.Start)]),
                EntityRef(KFirstEdge + Value.EdgeIndex),
                KeywordToken(
                    "forward"
                    if Frame.Edges[Value.EdgeIndex].StartCorner == Value.Start
                    else "reversed"
                ),
                EntityRef(KFirstLoop + Value.FaceIndex),
                0,
                EntityRef(-1),
            ),
        )
        for Value in UseValues
    )
