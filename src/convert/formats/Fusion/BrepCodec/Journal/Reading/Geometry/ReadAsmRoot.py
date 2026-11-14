from convert.formats.Fusion.BrepCodec.Journal.Geometry.AsmRoot import AsmRoot
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadRefMut import (
    ReadRefMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadTextMut import (
    ReadTextMut,
)


def ReadAsmRoot(Cursor: FieldCursor) -> AsmRoot:
    Attribute = ReadRefMut(Cursor)
    EntityTag = ReadLongMut(Cursor)
    KernelVersion = ReadTextMut(Cursor)
    return AsmRoot(Attribute, EntityTag, KernelVersion)
