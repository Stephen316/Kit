from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.NeedFieldMut import (
    NeedFieldMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadBoundMut import (
    ReadBoundMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadDoubleMut import (
    ReadDoubleMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadJumpsMut import (
    ReadJumpsMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadNubsSurf import (
    ReadNubsSurf,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadTransScope import (
    ReadTransScope,
)


def ReadTsplSurf(Cursor: FieldCursor) -> TsplineSurf:
    Revision = ReadLongMut(Cursor)
    if Revision <= 0:
        raise ValueError("Unsupported Fusion T-spline surface serializer form")
    NeedFieldMut(Cursor, (21, 0))
    Cache = ReadNubsSurf(Cursor)
    FitTolerance = ReadDoubleMut(Cursor)
    Jumps = ReadJumpsMut(Cursor, 6)
    NeedFieldMut(Cursor, (11, None))
    Ranges = (
        ReadBoundMut(Cursor),
        ReadBoundMut(Cursor),
        ReadBoundMut(Cursor),
        ReadBoundMut(Cursor),
    )
    TypeCode = ReadLongMut(Cursor, 21)
    Subtrans = ReadTransScope(Cursor)
    FaceIndex = ReadLongMut(Cursor)
    NeedFieldMut(Cursor, (16, None))
    return TsplineSurf(
        Revision, Cache, FitTolerance, Jumps, Ranges, TypeCode, Subtrans, FaceIndex
    )
