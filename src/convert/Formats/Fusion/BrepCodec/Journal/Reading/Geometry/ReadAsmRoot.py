from convert.Formats.Fusion.BrepCodec.Journal.Geometry.AsmRoot import AsmRoot
from convert.Formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadRefMut import (
    ReadRefMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadTextMut import (
    ReadTextMut,
)


# the asm root operation needs a distinct decoding boundary so revision ownership survives native history reconstruction
def ReadAsmRoot(Cursor: FieldCursor) -> AsmRoot:
    Attribute = ReadRefMut(Cursor)
    EntityTag = ReadLongMut(Cursor)
    KernelVersion = ReadTextMut(Cursor)
    return AsmRoot(Attribute, EntityTag, KernelVersion)
