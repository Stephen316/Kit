from convert.Formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.Formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


# the region use operation needs a consistent construction rule so topology identity survives native history reconstruction
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
