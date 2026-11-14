from convert.formats.Fusion.GeometryCodec.Prism.PrismLayout import (
    KEdgeCorners,
    KFaceCorners,
)
from convert.formats.Fusion.GeometryCodec.Prism.PrismUse import PrismUse


def BuildUses() -> tuple[PrismUse, ...]:
    EdgeIds = {Corners: Index for Index, Corners in enumerate(KEdgeCorners)}
    return tuple(
        PrismUse(
            Start,
            Finish,
            FaceIndex,
            RingIndex,
            EdgeIds[(min(Start, Finish), max(Start, Finish))],
        )
        for FaceIndex, Corners in enumerate(KFaceCorners)
        for RingIndex, (Start, Finish) in enumerate(
            zip(Corners, Corners[1:] + Corners[:1], strict=True)
        )
    )
