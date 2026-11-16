from convert.Formats.Fusion.HistoryRef import ReadNativeRef
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.SelectionProxy import SelectCursor

# each projection family begins with an explicitly owned controller
KProjController = "F1451EC8-11A4-4952-84ED-5AB7C13E2E83"

# the family controls the shape of the separately typed output entry
KProjEntry = "CA72DD8E-2861-4DDD-9721-03039B5FB113"


# the controller must agree with both the sketch owner and the selected input proxy
def ReadProjCtrl(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    ControllerId: int,
    FeatureId: int,
    ProxyId: int,
    FamilyCode: int,
) -> int:
    Controller = SelectCursor(BulkData, Owners, ControllerId, KProjController)
    if len(Controller.DataValue) != 105 or Controller.TakeBytes(6) != b"\0\0\1\0\0\1":
        raise ValueError("Unsupported Fusion sketch projection controller")
    EntryId = ReadNativeRef(Controller)
    Controller.Offset = 26
    if (
        Controller.ReadWord() != FamilyCode
        or ReadNativeRef(Controller) != FeatureId
        or ReadNativeRef(Controller) != ProxyId
    ):
        raise ValueError("Fusion projection controller and owner disagree")
    Controller.Offset = 94
    if ReadNativeRef(Controller) != FeatureId:
        raise ValueError("Fusion projection controller owner copy disagrees")
    return EntryId
