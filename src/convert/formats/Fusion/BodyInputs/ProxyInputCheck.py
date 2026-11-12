from convert.formats.Fusion.Extrudes.Plane.PlanePickSupport import (
    KProxySecondary,
    CheckPickLinks,
    ReadPickFooter,
)
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import KSelectProxy, SelectCursor


# repeated ordered support records corroborate the authored descriptor list
def CheckInputProxy(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    ProxyId: int,
    Descriptors: tuple[int, ...],
    ModeCode: int,
) -> None:
    Cursor = SelectCursor(BulkData, Owners, ProxyId, KSelectProxy)
    Cursor.Offset = len(Cursor.DataValue) - 88
    if Cursor.TakeBytes(2) != bytes(2) or Cursor.ReadWord() != 1:
        raise ValueError("Unsupported Fusion body proxy secondary count")
    Secondary = SelectCursor(BulkData, Owners, ReadNativeRef(Cursor), KProxySecondary)
    if Secondary.DataValue != b"\x00\x00\x01\x01\x00":
        raise ValueError("Unsupported Fusion body proxy secondary record")
    _, SupportId = ReadPickFooter(BulkData, Owners, Cursor, ModeCode=ModeCode)
    CheckPickLinks(BulkData, Owners, SupportId, ProxyId, Descriptors)
