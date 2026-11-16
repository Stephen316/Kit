from convert.Formats.Fusion.BrepCodec.Journal.Attributes.NoMergeAttrib import (
    NoMergeAttrib,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Attributes.ReadSysAttrib import (
    ReadSysLinks,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor


# the no merge operation needs a distinct decoding boundary so revision ownership survives native history reconstruction
def ReadNoMerge(Cursor: FieldCursor) -> NoMergeAttrib:
    return NoMergeAttrib(ReadSysLinks(Cursor))
