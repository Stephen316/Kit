from convert.formats.Fusion.SegmentCodec.Chronology.PackHistRefs import (
    PackHistRef,
    PackHistRefs,
)


# chronology order belongs to explicit record references rather than physical offsets
def EmitHistory(OwnerId: int, Entries: tuple[int, ...]) -> bytes:
    return bytes(6) + PackHistRef(OwnerId) + PackHistRefs(Entries)
