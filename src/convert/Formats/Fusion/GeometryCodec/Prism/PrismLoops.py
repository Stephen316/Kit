from convert.Formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.MakeRecord import MakeRecord
from convert.Formats.Fusion.GeometryCodec.Prism.PrismLayout import (
    KFaceCorners,
    KFirstCoedge,
    KFirstFace,
)


# the loops operation needs a consistent construction rule so geometric values retain their native record boundaries
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
