from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.IsLogicalMut import (
    IsLogicalMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadDoubleMut import (
    ReadDoubleMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadPrefixMut import (
    ReadPrefixMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadRefMut import (
    ReadRefMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadTextMut import (
    ReadTextMut,
)


def ReadEdgeNode(Cursor: FieldCursor) -> EdgeNode:
    Prefix = ReadPrefixMut(Cursor)
    StartVertex = ReadRefMut(Cursor)
    StartParam = ReadDoubleMut(Cursor)
    EndVertex = ReadRefMut(Cursor)
    EndParam = ReadDoubleMut(Cursor)
    OwnerCoedge = ReadRefMut(Cursor)
    CurveRef = ReadRefMut(Cursor)
    Reversed = IsLogicalMut(Cursor)
    Convexity = ReadTextMut(Cursor)
    return EdgeNode(
        Prefix,
        StartVertex,
        StartParam,
        EndVertex,
        EndParam,
        OwnerCoedge,
        CurveRef,
        Reversed,
        Convexity,
    )
