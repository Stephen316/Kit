from convert.formats.Fusion.Extrudes.ExtCacheOwner import CheckExtCache
from convert.formats.Fusion.Extrudes.ExtrudeInputs import ExtrudeInputs
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.NativeParam import NativeParam
from convert.formats.Fusion.NumericParam import KParamGuid, ReadNativeNum
from convert.formats.Fusion.ParamBinding import ResolveOwner
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor

# observed extrusion values use the real numeric binding class
KExtrudeBinding = "D91D429C-1BB5-4640-B49F-69AF14F463E9"


# owner and role checks keep unrelated numeric records out of distance controls
def CheckExtBinding(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    FeatureId: int,
    BindingId: int,
    RoleName: str,
) -> NativeParam:
    Cursor = SelectCursor(BulkData, Owners, BindingId, KExtrudeBinding)
    Cursor.Offset = 29
    ParamId = ReadNativeRef(Cursor)
    ParamCursor = SelectCursor(BulkData, Owners, ParamId, KParamGuid)
    ParamData = ReadNativeNum(ParamCursor.DataValue)
    if ParamData.BindingId != BindingId or ParamData.RoleName != RoleName:
        raise ValueError("Fusion Extrude numeric binding role or parameter disagrees")
    Resolved = ResolveOwner(BulkData, Owners, ParamData, Owners[ParamId])
    if Resolved is None or Resolved[0].ObjectId != FeatureId:
        raise ValueError("Fusion Extrude numeric binding owner disagrees")
    return ParamData


# independent cache and binding backlinks prove these values belong to the feature
def CheckExtInputs(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    FeatureId: int,
    Fields: ExtrudeInputs,
) -> None:
    CheckExtCache(BulkData, Owners, FeatureId, Fields.CacheId)
    ForAgainst = Fields.SecondTaperId if Fields.SideMode == "two_sided" else None
    Bindings = (
        (Fields.AlongId, "AlongDistance"),
        (Fields.AgainstId, "AgainstDistance"),
        (Fields.StartId, "ProfileOffset"),
        (Fields.TaperId, "TaperAngle"),
        (ForAgainst, "Side2TaperAngle"),
    )
    for Identity, RoleName in Bindings:
        if Identity is not None:
            _ = CheckExtBinding(BulkData, Owners, FeatureId, Identity, RoleName)
