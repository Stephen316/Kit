from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.NeedFieldMut import (
    NeedFieldMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadCountMut import (
    ReadCountMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadTextMut import (
    ReadTextMut,
)
from convert.formats.Fusion.BrepCodec.Models.FeatureTag import FeatureTag


def ReadTagGroups(Cursor: FieldCursor) -> tuple[FeatureTag, ...]:
    for Expected in ((4, 3), (4, 3), (4, -1), (7, "generic_tag_attrib_def ")):
        NeedFieldMut(Cursor, Expected)
    Groups: list[FeatureTag] = []
    for _ in range(ReadCountMut(Cursor, 32)):
        ByteCount = ReadCountMut(Cursor, 255)
        PrimaryId = ReadTextMut(Cursor)
        if ByteCount != len(PrimaryId.encode("ascii")):
            raise ValueError("Fusion primary identifier length disagrees")
        SecondaryId = ReadLongMut(Cursor)
        Operations = tuple(
            ReadLongMut(Cursor) for _ in range(ReadCountMut(Cursor, 256))
        )
        Groups.append(
            FeatureTag(PrimaryId, Operations, SecondaryId, ReadLongMut(Cursor))
        )
    return tuple(Groups)
