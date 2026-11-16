from convert.Formats.Fusion.Extrudes.ExtrudeBinding import CheckExtInputs
from convert.Formats.Fusion.Extrudes.ExtrudeControl import ReadExtControls
from convert.Formats.Fusion.Extrudes.ExtrudeProfile import ReadExtProfile
from convert.Formats.Fusion.Extrudes.NativeExtrude import NativeExtrude
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.SelectionProxy import SelectCursor

# a typed feature boundary limits every distance control read
KExtrudeGuid = "DD405BC2-D673-44F0-8833-5CB2A1C186C7"


# only qualified solid distance controls and an owned profile form a native extrude definition
def ReadExtrude(
    BulkData: bytes, Owners: dict[int, RecordSpan], FeatureId: int
) -> NativeExtrude:
    Cursor = SelectCursor(BulkData, Owners, FeatureId, KExtrudeGuid)
    Fields = ReadExtControls(Cursor)
    ProfileId, ProxyId = ReadExtProfile(
        BulkData, Owners, Cursor, FeatureId, Fields.SideMode
    )
    CheckExtInputs(BulkData, Owners, FeatureId, Fields)
    return NativeExtrude(
        Fields.AlongId,
        Fields.AgainstId,
        Fields.StartId,
        Fields.TaperId,
        Fields.SecondTaperId,
        Fields.SideMode,
        Fields.Direction,
        ProfileId,
        ProxyId,
    )
