from convert.formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


def BuildLoops() -> tuple[GeometryRecord, ...]:
    Values = ((8, 11, 4), (-1, 12, 4), (-1, 13, 5), (-1, 14, 6))
    return tuple(
        MakeRecord("loop", (EntityRef(NextLoop), EntityRef(Coedge), EntityRef(Owner)))
        for NextLoop, Coedge, Owner in Values
    )
