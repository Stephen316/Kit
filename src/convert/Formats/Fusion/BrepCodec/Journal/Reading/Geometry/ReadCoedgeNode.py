from convert.Formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.Formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.IsLogicalMut import (
    IsLogicalMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.NeedFieldMut import (
    NeedFieldMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadPrefixMut import (
    ReadPrefixMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadRefMut import (
    ReadRefMut,
)


# the coedge node operation needs a distinct decoding boundary so revision ownership survives native history reconstruction
def ReadCoedgeNode(Cursor: FieldCursor) -> CoedgeNode:
    Prefix = ReadPrefixMut(Cursor)
    NextCoedge = ReadRefMut(Cursor)
    PriorCoedge = ReadRefMut(Cursor)
    Partner = ReadRefMut(Cursor)
    EdgeRef = ReadRefMut(Cursor)
    Reversed = IsLogicalMut(Cursor)
    OwnerLoop = ReadRefMut(Cursor)
    NeedFieldMut(Cursor, (4, 0))
    Pcurve = ReadRefMut(Cursor)
    return CoedgeNode(
        Prefix,
        NextCoedge,
        PriorCoedge,
        Partner,
        EdgeRef,
        Reversed,
        OwnerLoop,
        Pcurve,
    )
