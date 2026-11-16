from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismFrame import PrismFrame
from convert.Formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.Formats.Fusion.GeometryCodec.MakeRecord import MakeRecord
from convert.Formats.Fusion.GeometryCodec.Prism.BuildUses import BuildUses
from convert.Formats.Fusion.GeometryCodec.Prism.PrismLayout import (
    KFirstCoedge,
    KFirstEdge,
    KFirstLoop,
)


# the prism coedges contract needs a shared interpretation so profile topology remains connected to its extrusion history
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
