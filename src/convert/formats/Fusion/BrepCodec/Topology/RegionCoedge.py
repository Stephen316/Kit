from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


def MakeRegionUse(Start: int) -> GeometryRecord:
    return MakeRecord(
        "coedge",
        (
            EntityRef(Start + 4),
            EntityRef(Start + 4),
            EntityRef(-1),
            EntityRef(Start + 5),
            KeywordToken("forward"),
            EntityRef(Start + 3),
            0,
            EntityRef(-1),
        ),
    )
