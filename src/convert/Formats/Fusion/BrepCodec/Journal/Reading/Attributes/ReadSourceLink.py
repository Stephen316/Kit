from convert.Formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.NeedFieldMut import (
    NeedFieldMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadTextMut import (
    ReadTextMut,
)
from convert.Formats.Fusion.BrepCodec.Models.SketchLink import SketchLink


# the source link operation needs a distinct decoding boundary so revision ownership survives native history reconstruction
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
