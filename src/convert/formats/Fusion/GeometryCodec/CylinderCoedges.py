from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


def BuildCoedges() -> tuple[GeometryRecord, ...]:
    Values = (
        (11, 13, 15, True, 7),
        (12, 14, 16, False, 8),
        (13, 11, 15, False, 9),
        (14, 12, 16, True, 10),
    )
    return tuple(
        MakeRecord(
            "coedge",
            (
                EntityRef(Index),
                EntityRef(Index),
                EntityRef(Partner),
                EntityRef(CurveEdge),
                KeywordToken("reversed" if Reverse else "forward"),
                EntityRef(Owner),
                0,
                EntityRef(-1),
            ),
        )
        for Index, Partner, CurveEdge, Reverse, Owner in Values
    )
