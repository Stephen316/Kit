from math import pi as KCircleHalf

from convert.formats.Fusion.GeometryCodec.CountedText import CountedText
from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


def MakeRegionEdge(Start: int) -> GeometryRecord:
    return MakeRecord(
        "edge",
        (
            EntityRef(Start + 6),
            -KCircleHalf,
            EntityRef(Start + 6),
            KCircleHalf,
            EntityRef(Start + 4),
            EntityRef(Start + 7),
            KeywordToken("forward"),
            CountedText("unknown"),
        ),
    )
