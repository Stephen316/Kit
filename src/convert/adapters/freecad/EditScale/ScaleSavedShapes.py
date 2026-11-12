from collections.abc import Mapping
from zipfile import ZipFile, ZipInfo

from convert.adapters.freecad.EditRead.Sketch.SavedSketchFiles import ReadShapeFile
from convert.adapters.freecad.EditRead.Sketch.SketchEvidence import CheckEmptyFile
from convert.adapters.freecad.EditShape.PrismShape import KMaxPrismBytes
from convert.adapters.freecad.EditShape.SavedSketchWire import KMaxSketchBytes
from convert.adapters.freecad.Native import NativeObject
from convert.adapters.freecad.ReconcileEdit import ReadEditBrep

# only the native sketch source and result nodes may contribute saved geometry
KScaleShapeLimits = {
    "Sketcher::SketchObject": KMaxSketchBytes,
    "Part::Extrusion": KMaxPrismBytes,
    "Part::Scale": KMaxPrismBytes,
}


# exact sidecar ownership prevents even geometrically identical bodies from exchanging bindings
def ReadScaleShapes(
    Archive: ZipFile,
    Members: Mapping[str, ZipInfo],
    Objects: Mapping[str, NativeObject],
) -> dict[str, bytes]:
    Shapes: dict[str, bytes] = {}
    Entries: set[str] = set()
    for Native in Objects.values():
        for Field, Property in Native.properties.items():
            if Property.get("type") != "Part::PropertyPartShape":
                continue
            Entry = ReadShapeFile(Native, Field)
            if Entry is None:
                continue
            if Entry != f"{Native.name}.{Field}.brp" or Entry not in Members:
                raise ValueError(
                    "FreeCAD editable Scale shape sidecar ownership changed"
                )
            Entries.add(Entry)
            Limit = KScaleShapeLimits.get(Native.type_id)
            if Field != "Shape" or Limit is None:
                CheckEmptyFile(Members, Entry)
            elif Members[Entry].file_size:
                Shapes[Native.name] = ReadEditBrep(
                    Archive, Members, Entry, Limit, "editable Scale"
                )
    if Entries != {
        NameValue for NameValue in Members if NameValue.lower().endswith(".brp")
    }:
        raise ValueError("FreeCAD editable Scale has additional shape sidecars")
    return Shapes
