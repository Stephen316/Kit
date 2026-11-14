from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.ReadFields import ReadFields
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgClassTable import DwgClassTable
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgObject import DwgObject
from convert.formats.Fusion.DrawingCodec.Dwg.Objects.NameObject import NameObject
from convert.formats.Fusion.DrawingCodec.Dwg.Objects.SplitObject import SplitObject
from convert.formats.Fusion.DrawingCodec.Dwg.Objects.TypeObject import TypeObject

KObjectMarker = 0x0DCA


def ReadObjects(
    DataValue: bytes, ClassTable: DwgClassTable, VersionText: str
) -> tuple[DwgObject, ...]:
    if ReadFields(DataValue, 0, "<I", "objects marker")[0] != KObjectMarker:
        raise ValueError("DWG object section does not start with its marker")
    DwgObjects: list[DwgObject] = []
    Offset = 4
    while Offset < len(DataValue):
        Generic, Offset = SplitObject(DataValue, Offset)
        ClassName, IsEntity = NameObject(Generic.TypeNumber, ClassTable)
        DwgObjects.append(TypeObject(Generic, ClassName, IsEntity, VersionText))
    return tuple(DwgObjects)
