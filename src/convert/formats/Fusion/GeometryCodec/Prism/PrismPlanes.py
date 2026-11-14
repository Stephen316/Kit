from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord
from convert.formats.Fusion.GeometryCodec.Prism.PrismLayout import KFaceCorners

KFaceFrames = (
    ((0.0, 0.0, -1.0), (0.0, 1.0, 0.0)),
    ((0.0, 0.0, 1.0), (1.0, 0.0, 0.0)),
    ((0.0, -1.0, 0.0), (1.0, 0.0, 0.0)),
    ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
    ((-1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
    ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
)


def BuildPlanes(
    Corners: tuple[tuple[float, float, float], ...],
) -> tuple[GeometryRecord, ...]:
    Bound = KeywordToken("I")
    return tuple(
        MakeRecord(
            "plane-surface",
            (
                Corners[Indices[0]],
                Normal,
                Basis,
                KeywordToken("forward_v"),
                Bound,
                Bound,
                Bound,
                Bound,
            ),
        )
        for Indices, (Normal, Basis) in zip(KFaceCorners, KFaceFrames, strict=True)
    )
