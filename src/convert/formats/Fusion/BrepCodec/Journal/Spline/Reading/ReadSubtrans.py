from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.NeedFieldMut import (
    NeedFieldMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtransNode import SubtransNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadPatches import (
    ReadPatches,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadWideText import (
    ReadWideText,
)
from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline


def ReadSubtrans(Cursor: FieldCursor) -> SubtransNode:
    Program = ReadWideText(Cursor).encode("ascii")
    NeedFieldMut(Cursor, (10, None))
    Patches = ReadWideText(Cursor)
    NeedFieldMut(Cursor, (16, None))
    Surface = ReadTspline(Program)
    if EmitTspline(Surface) != Program:
        raise ValueError("Noncanonical Fusion embedded T-spline program")
    return SubtransNode(Surface, ReadPatches(Patches))
