from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord
from convert.formats.Fusion.GeometryCodec.Prism.PrismLayout import (
    KFaceCorners,
    KFirstCoedge,
    KFirstFace,
)


def BuildLoops() -> tuple[GeometryRecord, ...]:
    return tuple(
        MakeRecord(
            "loop",
            (
                EntityRef(-1),
                EntityRef(KFirstCoedge + 4 * Index),
                EntityRef(KFirstFace + Index),
            ),
        )
        for Index in range(len(KFaceCorners))
    )
