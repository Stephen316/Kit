from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.GeometryValue import KGeometryValue
from convert.formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


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
