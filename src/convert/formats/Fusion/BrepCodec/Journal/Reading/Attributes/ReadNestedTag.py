from convert.formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks
from convert.formats.Fusion.BrepCodec.Journal.Attributes.NestedTag import (
    KNestedHead,
    NestedTag,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.NeedFieldMut import (
    NeedFieldMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)


def IsNestedForm(Cursor: FieldCursor) -> bool:
    Start = Cursor.Offset
    return Cursor.Record.Tokens[Start : Start + 7] == KNestedHead[:7]


def ReadNestedTag(Cursor: FieldCursor, Links: AttribLinks) -> NestedTag:
    if Links.NextAttrib != -1 or Links.PriorAttrib != -1:
        raise ValueError("Fusion nested tag attribute cannot join a sibling chain")
    for Expected in KNestedHead:
        NeedFieldMut(Cursor, Expected)
    OperationId = ReadLongMut(Cursor)
    NeedFieldMut(Cursor, (4, 0))
    return NestedTag(Links.OwnerRef, OperationId)
