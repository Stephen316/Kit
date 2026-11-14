from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord
from convert.formats.Fusion.GeometryCodec.Prism.PrismLayout import (
    KEdgeCorners,
    KFirstCoedge,
    KFirstEdge,
    KFirstLoop,
)
from convert.formats.Fusion.GeometryCodec.Prism.PrismUse import PrismUse


def BuildCoedges(UseValues: tuple[PrismUse, ...]) -> tuple[GeometryRecord, ...]:
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
                    if KEdgeCorners[Value.EdgeIndex][0] == Value.Start
                    else "reversed"
                ),
                EntityRef(KFirstLoop + Value.FaceIndex),
                0,
                EntityRef(-1),
            ),
        )
        for Value in UseValues
    )
