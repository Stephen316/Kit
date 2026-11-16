from struct import unpack as Unpack

from convert.Formats.Fusion.BodyInputs.CutInputs import ReadCutCount
from convert.Formats.Fusion.Extrudes.Cut.CutEndData import CutEndData
from convert.Formats.Fusion.HistoryRef import ReadNativeRef, ReadOptRefMut
from convert.Formats.Fusion.MetaCursor import MetaCursor
from interchange.Features.FeatureExtrude import ExtrudeEnd
from interchange.geometry.Models.VectorSpace import SpaceVector


# the saved end word and operands discriminate cut layouts with the same vector width
def ReadCutCtrlMut(Cursor: MetaCursor) -> CutEndData:
    Expected = ReadCutCount(Cursor.DataValue)
    if not Expected:
        raise ValueError("Unsupported Fusion one sided solid Cut header")
    Cursor.Offset = 27
    Direction = SpaceVector(*Unpack("<3d", Cursor.TakeBytes(24)))
    if Cursor.TakeBytes(2) != bytes(2):
        raise ValueError("Unsupported Fusion Cut start or against distance")
    AlongId = ReadOptRefMut(Cursor)
    CacheId = ReadNativeRef(Cursor)
    if Cursor.TakeBytes(1) != bytes(1):
        raise ValueError("Unsupported Fusion Cut second descriptor")
    TaperId = ReadNativeRef(Cursor)
    EndProxy = ReadOptRefMut(Cursor)
    EndCode = Cursor.ReadWord()
    if Cursor.TakeBytes(1) != bytes(1):
        raise ValueError("Unsupported Fusion Cut extent offset")
    FlagBits = Cursor.ReadWord()
    if Cursor.TakeBytes(16) != bytes(16):
        raise ValueError("Unsupported Fusion Cut secondary extent")
    if (
        (Expected, EndCode, FlagBits) == (7, 1, 0)
        and AlongId is not None
        and EndProxy is None
    ):
        EndValue = ExtrudeEnd.KBlind
    elif (
        (Expected, EndCode, FlagBits) == (8, 4, 2)
        and AlongId is None
        and EndProxy is not None
    ):
        EndValue = ExtrudeEnd.KThroughAll
    else:
        raise ValueError("Fusion Cut end code and operands disagree")
    return CutEndData(
        EndValue, FlagBits, Direction, AlongId, CacheId, TaperId, EndProxy
    )
