from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


def BuildFaces() -> tuple[GeometryRecord, ...]:
    Values = ((5, 7, 17, False), (6, 9, 18, False), (-1, 10, 19, True))
    return tuple(
        MakeRecord(
            "face",
            (
                EntityRef(NextFace),
                EntityRef(FirstLoop),
                EntityRef(3),
                EntityRef(-1),
                EntityRef(Surface),
                KeywordToken("reversed" if Reverse else "forward"),
                KeywordToken("single"),
            ),
        )
        for NextFace, FirstLoop, Surface, Reverse in Values
    )
