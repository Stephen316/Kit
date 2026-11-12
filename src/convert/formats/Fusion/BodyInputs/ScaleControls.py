from dataclasses import dataclass as MakeDataClass
from math import isfinite as IsFinite
from struct import unpack as Unpack

from convert.formats.Fusion.HistoryRef import ReadNativeRef, ReadOptRefMut
from convert.formats.Fusion.ParamBinding import KBindingWidths
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor

# body and sketch scales share a feature class but have differently typed operand lists
KScaleGuid = "D45FD6C4-161B-4240-BFAC-83A7C2C97A0C"


# native factor order and center identity remain available to the geometry reader
@MakeDataClass(frozen=True, slots=True)
class ScaleControls:
    FactorIds: tuple[int, ...]
    CenterId: int
    ProxyId: int
    CachedFactor: float


# the authored list follows a validated uniform or per axis factor layout
def ReadScaleData(
    BulkData: bytes, Owners: dict[int, RecordSpan], FeatureId: int
) -> ScaleControls:
    Cursor = SelectCursor(BulkData, Owners, FeatureId, KScaleGuid)
    if Cursor.TakeBytes(2) != bytes(2):
        raise ValueError("Unsupported Fusion Scale input prefix")
    (CachedFactor,) = Unpack("<d", Cursor.TakeBytes(8))
    CenterId = ReadNativeRef(Cursor)
    if not IsFinite(CachedFactor) or CenterId not in Owners:
        raise ValueError("Fusion Scale point or factor framing disagrees")
    Factor = ReadOptRefMut(Cursor)
    if Factor is None:
        if CachedFactor != 0 or Cursor.TakeBytes(6) != b"\x01" + bytes(5):
            raise ValueError("Unsupported Fusion nonuniform Scale input layout")
        Factors = tuple(ReadNativeRef(Cursor) for _ in range(3))
        if Cursor.ReadWord() != 1:
            raise ValueError("Fusion Scale input collection count changed")
    else:
        if Cursor.TakeBytes(13) != bytes.fromhex("01000000000100000001000000"):
            raise ValueError("Unsupported Fusion uniform Scale input layout")
        Factors = (Factor,)
    if any(
        Identity not in Owners or Owners[Identity].ClassGuid not in KBindingWidths
        for Identity in Factors
    ):
        raise ValueError("Fusion Scale factor binding is missing")
    return ScaleControls(Factors, CenterId, ReadNativeRef(Cursor), CachedFactor)
