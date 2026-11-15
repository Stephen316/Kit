from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadFieldMut import (
    ReadFieldMut,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import KAsmToken


# invalid field input must fail here so revision ownership survives native history reconstruction
def NeedFieldMut(Cursor: FieldCursor, Expected: KAsmToken) -> None:
    if ReadFieldMut(Cursor) != Expected:
        raise ValueError("Unsupported Fusion journal qualified field")
