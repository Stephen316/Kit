from convert.formats.Fusion.Extrudes.ExtrudeBinding import KExtrudeBinding
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.NativeParam import NativeParam
from convert.formats.Fusion.ParamBinding import ResolveOwner
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Topology.PickSupport import KSupportGuid


# a typed support backlink proves the binding pointer without classifying the raw timestamp
def CheckBindBook(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    BookId: int,
    BindingId: int,
) -> None:
    BookValue = Owners.get(BookId)
    if (
        BookValue is None
        or not BookValue.IsPrimary
        or BookValue.ClassGuid != KSupportGuid
    ):
        raise ValueError("Missing typed Fusion binding bookkeeping")
    Cursor = MetaCursor(BulkData[BookValue.PayloadOffset : BookValue.EndOffset])
    if (
        len(Cursor.DataValue) != 43
        or Cursor.TakeBytes(16) != bytes(16)
        or ReadNativeRef(Cursor) != BindingId
        or Cursor.TakeBytes(16)[8:] != bytes(8)
    ):
        raise ValueError("Fusion binding bookkeeping backlink or framing disagrees")


# every binding byte needs checked framing identity or a separately corroborated value
def ReadBindRecord(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    ParamData: NativeParam,
    ParamSpan: RecordSpan,
    BoundRank: int,
) -> tuple[RecordSpan, RecordSpan, int]:
    PairValue = ResolveOwner(BulkData, Owners, ParamData, ParamSpan)
    if PairValue is None:
        raise ValueError("Fusion numeric parameter has no binding")
    OwnerValue, Binding = PairValue
    if (
        not Binding.IsPrimary
        or not OwnerValue.IsPrimary
        or Binding.ClassGuid != KExtrudeBinding
    ):
        raise ValueError("Unsupported Fusion numeric binding proof dialect")
    Cursor = MetaCursor(BulkData[Binding.PayloadOffset : Binding.EndOffset])
    if (
        Cursor.TakeBytes(9) != bytes(4) + b"\1\1\0\0\0"
        or ReadNativeRef(Cursor) != OwnerValue.ObjectId
    ):
        raise ValueError("Unsupported Fusion binding header or owner reference")
    SlotValue = Cursor.ReadWord()
    if Cursor.TakeBytes(1) != bytes(1):
        raise ValueError("Unsupported Fusion numeric binding slot framing")
    _ = Cursor.TakeBytes(8)
    if (
        ReadNativeRef(Cursor) != ParamSpan.ObjectId
        or Cursor.ReadWord() != BoundRank
        or Cursor.TakeBytes(4) != bytes(4)
        or ReadNativeRef(Cursor) != OwnerValue.ObjectId
        or Cursor.TakeBytes(3) != b"\1\0\0"
    ):
        raise ValueError("Fusion binding parameter rank or repeated owner disagrees")
    BookId = ReadNativeRef(Cursor)
    if (
        Cursor.TakeBytes(1) != bytes(1)
        or ReadNativeRef(Cursor) != OwnerValue.ObjectId
        or Cursor.Offset != len(Cursor.DataValue)
    ):
        raise ValueError(
            "Fusion binding bookkeeping or terminal owner framing disagrees"
        )
    CheckBindBook(BulkData, Owners, BookId, Binding.ObjectId)
    return OwnerValue, Binding, SlotValue
