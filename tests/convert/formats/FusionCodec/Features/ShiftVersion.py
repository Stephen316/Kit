from dataclasses import replace as Replace

from convert.formats.Fusion.SegmentCodec.Metadata.MetaSegment import MetaSegment


def ShiftVersion(Metadata: MetaSegment, ClassGuid: str) -> MetaSegment:
    Matches = tuple(
        Entry
        for Entry in Metadata.Classes
        if Entry.ClassGuid.upper() == ClassGuid.upper()
    )
    assert len(Matches) == 1
    Target = Matches[0]
    Classes = tuple(
        (
            Replace(Entry, SchemaVersion=Entry.SchemaVersion + 1)
            if Entry is Target
            else Entry
        )
        for Entry in Metadata.Classes
    )
    return Replace(Metadata, Classes=Classes)
