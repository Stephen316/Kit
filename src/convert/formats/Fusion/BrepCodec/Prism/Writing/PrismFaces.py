from convert.formats.Fusion.BrepCodec.Prism.Models.PrismFrame import PrismFrame
from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord
from convert.formats.Fusion.GeometryCodec.Prism.PrismLayout import (
    KFaceCorners,
    KFirstCoedge,
    KFirstFace,
    KFirstLoop,
    KFirstPlane,
)


def PrismFaces(Frame: PrismFrame) -> tuple[GeometryRecord, ...]:
    Following = dict(zip(Frame.FaceOrder, Frame.FaceOrder[1:] + (-1,), strict=True))
    return tuple(
        MakeRecord(
            "face",
            (
                EntityRef(
                    KFirstFace + Following[Index] if Following[Index] != -1 else -1
                ),
                EntityRef(KFirstLoop + Index),
                EntityRef(3),
                EntityRef(-1),
                EntityRef(KFirstPlane + Index),
                KeywordToken("reversed" if Frame.FaceReverse[Index] else "forward"),
                KeywordToken("single"),
            ),
        )
        for Index in range(6)
    )


def PrismLoops(Frame: PrismFrame) -> tuple[GeometryRecord, ...]:
    return tuple(
        MakeRecord(
            "loop",
            (
                EntityRef(-1),
                EntityRef(
                    KFirstCoedge
                    + 4 * Index
                    + KFaceCorners[Index].index(Frame.FaceStarts[Index])
                ),
                EntityRef(KFirstFace + Index),
            ),
        )
        for Index in range(6)
    )
