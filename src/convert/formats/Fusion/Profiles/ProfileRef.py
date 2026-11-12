from uuid import UUID

from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor

# typed profile descriptors explicitly identify their consuming feature
KProfileGuid = "4BD53E5A-0B3E-45E5-AE8B-02044306485A"

# loop ownership is checked independently of the forward descriptor link
KLoopGuid = "0D57BD2F-D09B-43FC-AD57-1E89A118C453"


# one cursor rule keeps descriptor and projection owner framing consistent
def DescOwner(BodyValue: bytes) -> int:
    Cursor = MetaCursor(BodyValue)
    Cursor.Offset = len(BodyValue) - 11
    return ReadNativeRef(Cursor)


# native profile descriptors select a sketch and its separate loop record
def ReadProfileRef(BodyValue: bytes) -> tuple[int, int]:
    Cursor = MetaCursor(BodyValue)
    if Cursor.TakeBytes(2) != bytes(2):
        raise ValueError("Invalid Fusion profile descriptor prefix")
    LoopId = ReadNativeRef(Cursor)
    if Cursor.ReadWord() != 1:
        raise ValueError("Unsupported Fusion profile descriptor count")
    Namespace = Cursor.ReadText(True, Maximum=36)
    _ = UUID(Namespace)
    SketchText = Cursor.ReadText(True, Maximum=20)
    if len(Namespace) != 36 or not SketchText.isascii() or not SketchText.isdecimal():
        raise ValueError("Invalid Fusion profile sketch identity")
    return int(SketchText), LoopId
