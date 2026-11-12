from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SelectionProxy import SelectCursor
from interchange.enums.EnumGeometry import GeometryKind
from interchange.geometry.models.Sketch import Sketch, SketchEntity

# the sketch leaf names a root and entity tag instead of a geometry record id
KSketchLeaf = "E2CEFD18-D755-4E09-8E7F-953A2F6D43F8"


# the bounded leaf separates the selected root from the root local curve tag
def ReadSketchPick(
    BulkData: bytes, Owners: dict[int, RecordSpan], Terminal: int
) -> tuple[int, int]:
    Cursor = SelectCursor(BulkData, Owners, Terminal, KSketchLeaf)
    if len(Cursor.DataValue) != 26 or Cursor.TakeBytes(10) != bytes(10):
        raise ValueError("Unsupported Fusion sketch selection leaf")
    return Cursor.ReadLong(), Cursor.ReadLong()


# curve tags are scoped to one already qualified sketch root
def FindSketchCurve(SketchValue: Sketch, TagValue: int) -> SketchEntity:
    Matches = tuple(
        Entity
        for Entity in SketchValue.entities
        if Entity.kind != GeometryKind.KPoint
        and Entity.attributes.get("fusion.entity_tag") == TagValue
    )
    if len(Matches) != 1:
        raise ValueError("Missing or ambiguous Fusion sketch selection tag")
    return Matches[0]
