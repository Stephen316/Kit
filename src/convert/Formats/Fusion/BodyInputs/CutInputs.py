from convert.Formats.Fusion.BodyInputs.BodyInput import BodyInputs
from convert.Formats.Fusion.BodyInputs.InputRefs import ReadInputPicks, ReadPickRefs
from convert.Formats.Fusion.Extrudes.ExtrudeRead import KExtrudeGuid
from convert.Formats.Fusion.HistoryRef import ReadNativeRef, ReadOptRefMut
from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.SelectionProxy import KSelectProxy, SelectCursor
from convert.Formats.Fusion.Topology.BodyPick import KCutTargetMode
from interchange.Enums.EnumFeatures import BooleanOp


# ordinary extrusions must stay outside the cut specific historical body selector
def ReadCutCount(BodyValue: bytes) -> int:
    if len(BodyValue) not in (446, 467):
        return 0
    Cursor = MetaCursor(BodyValue)
    if (
        Cursor.TakeBytes(9) != b"\0\1" + bytes(7)
        or Cursor.ReadWord() != 2
        or Cursor.ReadWord() != 1
        or Cursor.ReadWord() != (2 if len(BodyValue) == 446 else 1)
        or Cursor.TakeBytes(6) != b"\0\1" + bytes(4)
    ):
        return 0
    return 7 if len(BodyValue) == 446 else 8


# the authored target list has its own proxy even when the extent references a body
def ReadCutInputs(
    BulkData: bytes, Owners: dict[int, RecordSpan], FeatureId: int
) -> BodyInputs:
    Cursor = SelectCursor(BulkData, Owners, FeatureId, KExtrudeGuid)
    Expected = ReadCutCount(Cursor.DataValue)
    if not Expected:
        raise ValueError("Unsupported Fusion Cut target body layout")
    Cursor.Offset = 155
    Proxies = ReadPickRefs(Cursor, Owners, KSelectProxy)
    if len(Proxies) != 1:
        raise ValueError("Fusion Cut requires one owned target body proxy")
    (ProxyId,) = Proxies
    Picks = ReadInputPicks(
        BulkData, Owners, FeatureId, ProxyId, "target", KCutTargetMode
    )
    if len(Picks) != 1:
        raise ValueError("Fusion Cut requires one whole target body")
    Cursor.Offset = 249
    if Cursor.ReadCount(8) != Expected:
        raise ValueError("Unexpected Fusion Cut dependency count")
    Dependencies = tuple(ReadNativeRef(Cursor) for _ in range(Expected))
    if len(set(Dependencies)) != Expected or Dependencies[:2] != (
        ProxyId,
        Picks[0].DescriptorId,
    ):
        raise ValueError("Fusion Cut target dependency copies disagree")
    Cursor.Offset = 77 if Expected == 8 else 87
    ExtentId = ReadOptRefMut(Cursor)
    if (ExtentId is not None) != (Expected == 8) or ExtentId == ProxyId:
        raise ValueError("Fusion Cut target and extent selectors overlap")
    if ExtentId is not None:
        _ = SelectCursor(BulkData, Owners, ExtentId, KSelectProxy)
        if ExtentId not in Dependencies:
            raise ValueError("Fusion Cut extent selector lacks its dependency")
    return BodyInputs(Picks, BooleanOp.KCutOperation)
