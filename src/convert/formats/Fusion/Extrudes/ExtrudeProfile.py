from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.Profiles.ProfileRef import (
    DescOwner,
    KLoopGuid,
    KProfileGuid,
    ReadProfileRef,
)
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import ReadSelectDesc, SelectCursor

# the sketch entity registry distinguishes sketch profile sources from arbitrary records
KExtrudeSketch = "44A64366-4BD3-4B24-881A-F94C206E8F2D"


# the wall boundary locates the owned proxy without guessing from nearby records
def ReadExtProfile(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    Cursor: MetaCursor,
    FeatureId: int,
    SideMode: str,
) -> tuple[int, int]:
    WallWidth = 11 if SideMode.startswith("symmetric_") else 15
    if Cursor.TakeBytes(WallWidth) != bytes(WallWidth):
        raise ValueError("Unsupported thin Fusion Extrude or active wall controls")
    if Cursor.ReadWord() != 1:
        raise ValueError("Fusion distance Extrude requires one profile selection")
    ProxyId = ReadNativeRef(Cursor)
    ProfileId = ReadSelectDesc(BulkData, Owners, ProxyId, FeatureId)
    Profile = SelectCursor(BulkData, Owners, ProfileId, KProfileGuid)
    if DescOwner(Profile.DataValue) != FeatureId:
        raise ValueError("Fusion Extrude profile descriptor owner disagrees")
    SketchId, LoopId = ReadProfileRef(Profile.DataValue)
    _ = SelectCursor(BulkData, Owners, SketchId, KExtrudeSketch)
    LoopValue = SelectCursor(BulkData, Owners, LoopId, KLoopGuid)
    if LoopValue.TakeBytes(2) != bytes(2) or ReadNativeRef(LoopValue) != ProfileId:
        raise ValueError("Fusion Extrude profile loop owner disagrees")
    return ProfileId, ProxyId
