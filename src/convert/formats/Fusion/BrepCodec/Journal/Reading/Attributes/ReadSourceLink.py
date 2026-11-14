from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.NeedFieldMut import (
    NeedFieldMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadTextMut import (
    ReadTextMut,
)
from convert.formats.Fusion.BrepCodec.Models.SketchLink import SketchLink


def ReadSourceLink(Cursor: FieldCursor) -> SketchLink:
    for Expected in ((4, 1), (4, 1), (4, 3)):
        NeedFieldMut(Cursor, Expected)
    Words = ReadTextMut(Cursor).split(" ")
    if len(Words) != 6:
        raise ValueError("Invalid Fusion journal sketch source link")
    Values = tuple(int(Value) for Value in Words)
    if tuple(str(Value) for Value in Values) != tuple(Words):
        raise ValueError("Unsupported Fusion sketch integer spelling")
    return SketchLink(Values[0], Values[1], Values[2], Values[4], Values[5], Values[3])
