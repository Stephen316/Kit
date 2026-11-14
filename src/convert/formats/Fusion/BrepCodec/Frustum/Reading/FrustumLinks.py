from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmPtr
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmRecord


def FrustumLinks(
    Wanted: AsmRecord, Stored: AsmRecord, RecordCount: int
) -> tuple[tuple[int, int], ...]:
    IsAttribute = Wanted.Name == "ATTRIB_CUSTOM-attrib"
    Count = 5 if IsAttribute else len(Wanted.Tokens)
    if Wanted.Name != Stored.Name or (
        len(Stored.Tokens) < Count if IsAttribute else len(Stored.Tokens) != Count
    ):
        raise ValueError("Unsupported frustum topology record")
    Pairs: list[tuple[int, int]] = []
    for Index in range(Count):
        ExpectedTag, StoredTag = Wanted.Tokens[Index][0], Stored.Tokens[Index][0]
        if ExpectedTag != StoredTag and {ExpectedTag, StoredTag} != {10, 11}:
            raise ValueError("Frustum topology field type disagrees")
        if ExpectedTag != 12:
            continue
        ExpectedRef, ActualRef = ReadAsmPtr(Wanted, Index), ReadAsmPtr(Stored, Index)
        if ExpectedRef == -1 or ActualRef == -1:
            if ExpectedRef != ActualRef:
                raise ValueError("Frustum topology null link disagrees")
            continue
        if not 0 <= ActualRef < RecordCount:
            raise ValueError("Frustum topology link leaves the entity table")
        Pairs.append((ExpectedRef, ActualRef))
    return tuple(Pairs)
