from convert.Formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord
from convert.Formats.Fusion.GeometryCodec.MakeRecord import MakeRecord


# the loops operation needs a consistent construction rule so geometric values retain their native record boundaries
def BuildLoops() -> tuple[GeometryRecord, ...]:
    Values = ((8, 11, 4), (-1, 12, 4), (-1, 13, 5), (-1, 14, 6))
    return tuple(
        MakeRecord("loop", (EntityRef(NextLoop), EntityRef(Coedge), EntityRef(Owner)))
        for NextLoop, Coedge, Owner in Values
    )
