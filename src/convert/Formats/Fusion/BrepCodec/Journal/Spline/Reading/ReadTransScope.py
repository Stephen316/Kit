from convert.Formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.Formats.Fusion.BrepCodec.Journal.Spline.SubtransNode import SubtransNode
from convert.Formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef
from convert.Formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadScopeMut import (
    ReadScopeMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadSubtrans import (
    ReadSubtrans,
)


# the trans scope operation needs a distinct decoding boundary so topology changes retain their native revision relationships
def ReadTransScope(Cursor: FieldCursor) -> SubtransNode | SubtypeRef:
    Scope = ReadScopeMut(Cursor, "subtrans")
    if isinstance(Scope, SubtypeRef):
        return Scope
    if Scope != "t_spl_subtrans_object":
        raise ValueError("Unsupported Fusion T-spline subtransform subtype")
    return ReadSubtrans(Cursor)
