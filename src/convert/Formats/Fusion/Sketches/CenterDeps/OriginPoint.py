from convert.Formats.Fusion.HistoryRef import ReadNativeRef
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.Revolves.OriginAxis import KComponentGuid, KOriginGuid
from convert.Formats.Fusion.SelectionProxy import SelectCursor
from convert.Formats.Fusion.Sketches.GeometryAttrs import ReadGeomAttrs

# origin point geometry is typed separately from an ordinary sketch coordinate
KOriginPoint = "0E18EEF2-0D6F-480C-997E-5EBC7369AE5F"


# reciprocal component ownership distinguishes this origin from a coincident point
def ReadOriginPoint(
    BulkData: bytes, Owners: dict[int, RecordSpan], PointId: int, ComponentId: int
) -> int:
    Point = SelectCursor(BulkData, Owners, PointId, KOriginPoint)
    if len(Point.DataValue) != 146 or ReadGeomAttrs(Point) != {"EntityGenesis": 0}:
        raise ValueError("Unsupported Fusion component origin point layout")
    Start = Point.Offset
    if Point.TakeBytes(24) != bytes(24):
        raise ValueError("Fusion component origin point is displaced")
    Point.Offset = Start + 34
    if Point.ReadText(True, Maximum=1) != "O":
        raise ValueError("Fusion origin point name disagrees")
    Point.Offset = len(Point.DataValue) - 11
    ContainerId = ReadNativeRef(Point)
    Container = SelectCursor(BulkData, Owners, ContainerId, KOriginGuid)
    if (
        len(Container.DataValue) != 96
        or Container.TakeBytes(4) != bytes(4)
        or Container.ReadWord() != 7
    ):
        raise ValueError("Unsupported Fusion origin point container")
    Members = {ReadNativeRef(Container) for _ in range(7)}
    Component = SelectCursor(BulkData, Owners, ComponentId, KComponentGuid)
    Component.Offset = 66
    if (
        len(Members) != 7
        or PointId not in Members
        or not Members <= Owners.keys()
        or ReadNativeRef(Container) != ComponentId
        or ReadNativeRef(Component) != ContainerId
    ):
        raise ValueError("Fusion origin point and component ownership disagree")
    return ContainerId
