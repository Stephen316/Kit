from convert.Formats.Fusion.HistoryRef import ReadNativeRef
from convert.Formats.Fusion.NativePlane import KPlaneObject
from convert.Formats.Fusion.PlaneAxes import ReadPlaneAxes
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.Revolves.OriginAxis import KOriginGuid
from convert.Formats.Fusion.SelectionProxy import SelectCursor
from convert.Formats.Fusion.Sketches.GeometryAttrs import ReadGeomAttrs
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector

# origin labels and normals jointly distinguish supported component datum planes
KOriginNormals = {
    "XY": SpaceVector(0.0, 0.0, 1.0),
    "XZ": SpaceVector(0.0, 1.0, 0.0),
    "YZ": SpaceVector(1.0, 0.0, 0.0),
}


# origin datum membership proves the explicit support stays inside the same component
def ReadOffsetOrg(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    OriginId: int,
    ComponentId: int,
) -> tuple[Transform, int]:
    Cursor = SelectCursor(BulkData, Owners, OriginId, KPlaneObject)
    if len(Cursor.DataValue) != 233 or ReadGeomAttrs(Cursor) != {"EntityGenesis": 0}:
        raise ValueError("Unsupported Fusion Offset origin plane attributes")
    Start = Cursor.Offset
    if Cursor.ReadWord() != 0:
        raise ValueError("Unsupported Fusion Offset origin plane type")
    _ = Cursor.TakeBytes(16)
    if Cursor.TakeBytes(1) != bytes(1):
        raise ValueError("Unsupported Fusion Offset origin plane frame marker")
    Frame = ReadPlaneAxes(Cursor.TakeBytes(72))
    Cursor.Offset = Start + 119
    NameValue = Cursor.ReadText(True, Maximum=2)
    if (
        Frame.origin != SpaceVector(0.0, 0.0, 0.0)
        or KOriginNormals.get(NameValue) != Frame.z_axis
    ):
        raise ValueError("Fusion Offset origin datum name or frame disagrees")
    Cursor.Offset = len(Cursor.DataValue) - 11
    ContainerId = ReadNativeRef(Cursor)
    Container = SelectCursor(BulkData, Owners, ContainerId, KOriginGuid)
    if (
        len(Container.DataValue) != 96
        or Container.TakeBytes(4) != bytes(4)
        or Container.ReadWord() != 7
    ):
        raise ValueError("Unsupported Fusion Offset origin datum container")
    Members = {ReadNativeRef(Container) for _ in range(7)}
    if (
        len(Members) != 7
        or OriginId not in Members
        or any(Identity not in Owners for Identity in Members)
        or ReadNativeRef(Container) != ComponentId
    ):
        raise ValueError("Fusion Offset origin datum component membership disagrees")
    return Frame, ContainerId
