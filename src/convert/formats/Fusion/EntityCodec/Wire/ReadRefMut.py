from convert.formats.Fusion.EntityCodec.Model.CrossRef import CrossRef
from convert.formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Wire.ReadAtomMut import ReadAtomMut
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef

KMaxTypeText = 37

KInlineType = b"\x24"


def ReadRefMut(Cursor: MetaCursor) -> LocalRef | SegmentRef | CrossRef | None:
    if not ReadAtomMut(Cursor, WireType("bool")):
        return None
    ObjectId = Cursor.ReadLong()
    CrossFlag = Cursor.TakeBytes(1)
    if CrossFlag == KInlineType:
        raise ValueError("Unsupported inline-typed Fusion entity reference")
    if CrossFlag not in (b"\0", b"\1"):
        raise ValueError("Invalid Fusion entity reference flag")
    if CrossFlag == b"\1":
        Token = Cursor.ReadLong()
        if Cursor.TakeBytes(1) != b"\0":
            raise ValueError("Unsupported Fusion cross-document reference form")
        TypeGuid = Cursor.ReadText(Maximum=KMaxTypeText)
        if Cursor.TakeBytes(1) != b"\0" or len(TypeGuid) not in (36, 37):
            raise ValueError("Unsupported Fusion cross-document reference form")
        return CrossRef(ObjectId, Token, TypeGuid)
    if ReadAtomMut(Cursor, WireType("bool")):
        return SegmentRef(ObjectId, Cursor.ReadWord())
    return LocalRef(ObjectId)
