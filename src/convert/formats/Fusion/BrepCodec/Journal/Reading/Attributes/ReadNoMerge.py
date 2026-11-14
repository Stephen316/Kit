from convert.formats.Fusion.BrepCodec.Journal.Attributes.NoMergeAttrib import (
    NoMergeAttrib,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Attributes.ReadSysAttrib import (
    ReadSysLinks,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor


def ReadNoMerge(Cursor: FieldCursor) -> NoMergeAttrib:
    return NoMergeAttrib(ReadSysLinks(Cursor))
