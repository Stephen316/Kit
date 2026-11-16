from convert.Formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


# the region uses contract needs a shared interpretation so supporting records retain their owning document relationships
def RegionUses(Start: int) -> tuple[GeometryRecord, ...]:
    return tuple(
        MakeRecord(
            "coedge",
            (
                EntityRef(Start + 5 + (Index + 1) % 4),
                EntityRef(Start + 5 + (Index - 1) % 4),
                EntityRef(-1),
                EntityRef(Start + 9 + Index),
                False,
                EntityRef(Start + 3),
                0,
                EntityRef(-1),
            ),
        )
        for Index in range(4)
    )
