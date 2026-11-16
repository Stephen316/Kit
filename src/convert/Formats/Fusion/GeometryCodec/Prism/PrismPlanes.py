from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.KeywordToken import KeywordToken
from convert.Formats.Fusion.GeometryCodec.MakeRecord import MakeRecord
from convert.Formats.Fusion.GeometryCodec.Prism.PrismLayout import KFaceCorners

# the face frames order must stay explicit so geometric values retain their native record boundaries
KFaceFrames = (
    ((0.0, 0.0, -1.0), (0.0, 1.0, 0.0)),
    ((0.0, 0.0, 1.0), (1.0, 0.0, 0.0)),
    ((0.0, -1.0, 0.0), (1.0, 0.0, 0.0)),
    ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
    ((-1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
    ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
)


# the planes operation needs a consistent construction rule so geometric values retain their native record boundaries
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
