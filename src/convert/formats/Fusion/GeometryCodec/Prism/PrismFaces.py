from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord
from convert.formats.Fusion.GeometryCodec.Prism.PrismLayout import (
    KFaceCorners,
    KFirstFace,
    KFirstLoop,
    KFirstPlane,
)


# the faces operation needs a consistent construction rule so geometric values retain their native record boundaries
def BuildFaces() -> tuple[GeometryRecord, ...]:
    return tuple(
        MakeRecord(
            "face",
            (
                EntityRef(
                    KFirstFace + Index + 1 if Index + 1 < len(KFaceCorners) else -1
                ),
                EntityRef(KFirstLoop + Index),
                EntityRef(3),
                EntityRef(-1),
                EntityRef(KFirstPlane + Index),
                KeywordToken("forward"),
                KeywordToken("single"),
            ),
        )
        for Index in range(len(KFaceCorners))
    )
