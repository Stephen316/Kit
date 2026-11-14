from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


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
