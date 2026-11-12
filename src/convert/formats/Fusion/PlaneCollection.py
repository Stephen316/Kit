from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.NativePlane import KPlaneObject
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor
from interchange.geometry.models.SupportPlane import SupportPlane

# construction geometry repeats its membership before naming the owning component
KDatumCollection = "A8635B5F-1E2C-45FD-8BA9-0173B0FEB75E"

# the collection must end in a typed component rather than another datum
KDatumComponent = "E03784ED-5E19-4E14-B9F2-3B07017018CD"


# reciprocal plane and collection records prove the component scope of the frame
def ReadPlaneComp(
    BulkData: bytes, Owners: dict[int, RecordSpan], PlaneValue: SupportPlane
) -> tuple[int, int]:
    if PlaneValue.provenance is None:
        raise ValueError("Missing Fusion construction plane provenance")
    PlaneId = int(PlaneValue.provenance.native_id)
    Cursor = SelectCursor(BulkData, Owners, PlaneId, KPlaneObject)
    TailValue = MetaCursor(Cursor.DataValue[-11:])
    CollectionId = ReadNativeRef(TailValue)
    if CollectionId != PlaneValue.attributes.get("fusion.plane_collection_id"):
        raise ValueError("Fusion construction plane collection references disagree")
    Cursor = SelectCursor(BulkData, Owners, CollectionId, KDatumCollection)
    if Cursor.TakeBytes(2) != bytes(2):
        raise ValueError("Unsupported Fusion construction collection prefix")
    Count = Cursor.ReadCount(100000)
    if len(Cursor.DataValue) != 51 + 22 * Count:
        raise ValueError("Unsupported Fusion construction collection width")
    Members = tuple(ReadNativeRef(Cursor) for _ in range(Count))
    if PlaneId not in Members or len(set(Members)) != Count:
        raise ValueError("Missing or duplicate Fusion construction collection member")
    _ = Cursor.TakeBytes(30)
    if (
        Cursor.ReadWord() != Count
        or tuple(ReadNativeRef(Cursor) for _ in range(Count)) != Members
    ):
        raise ValueError("Fusion construction collection membership disagrees")
    ComponentId = ReadNativeRef(Cursor)
    Component = Owners.get(ComponentId)
    if Component is None or Component.ClassGuid != KDatumComponent:
        raise ValueError("Missing typed Fusion construction collection component")
    return ComponentId, CollectionId
