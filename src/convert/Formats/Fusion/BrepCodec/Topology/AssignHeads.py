from dataclasses import replace as Replace

from convert.Formats.Fusion.GeometryCodec.EntityRef import EntityRef
from convert.Formats.Fusion.GeometryCodec.GeometryRecord import GeometryRecord


# assign heads needs an explicit validity boundary so topology identity survives native history reconstruction
def AssignHeads(
    Records: tuple[GeometryRecord, ...], Links: tuple[tuple[int, int], ...]
) -> tuple[GeometryRecord, ...]:
    Values = list(Records)
    if len({LinkValue[0] for LinkValue in Links}) != len(Links):
        raise ValueError("Fusion BRep attribute owners must be unique")
    for Owner, AttrHead in Links:
        if not 0 <= Owner < len(Values) or not Values[Owner].Fields:
            raise ValueError("Fusion BRep attribute owner leaves the topology table")
        Record = Values[Owner]
        Values[Owner] = Replace(
            Record, Fields=(EntityRef(AttrHead), *Record.Fields[1:])
        )
    return tuple(Values)
