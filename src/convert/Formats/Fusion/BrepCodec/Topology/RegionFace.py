from convert.Formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.GeometryValue import KGeometryValue
from convert.Formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.Formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


# the region face operation needs a consistent construction rule so topology identity survives native history reconstruction
def MakeRegionFace(Start: int, IsDouble: bool) -> GeometryRecord:
    Fields: tuple[KGeometryValue, ...] = (
        EntityRef(-1),
        EntityRef(Start + 3),
        EntityRef(Start + 1),
        EntityRef(-1),
        EntityRef(Start + 8),
        KeywordToken("forward"),
        IsDouble,
    )
    if IsDouble:
        Fields += (False,)
    return MakeRecord("face", Fields)
