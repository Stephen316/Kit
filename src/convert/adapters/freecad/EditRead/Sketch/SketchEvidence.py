from collections.abc import Mapping
from zipfile import ZipFile, ZipInfo

from convert.adapters.freecad.EditRead.EditParts import ReadPartEntry
from convert.adapters.freecad.EditRead.Sketch.SavedSketchFiles import ReadSketchFiles
from convert.adapters.freecad.EditShape.SavedSketchWire import (
    IsSketchCache,
    KMaxSketchBytes,
)
from convert.adapters.freecad.Native import NativeObject
from convert.adapters.freecad.ReconcileEdit import ReadEditBrep
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.Transform import Transform


# auxiliary timeline and internal shapes must not introduce another geometry result
def CheckEmptyFile(Members: Mapping[str, ZipInfo], NameValue: str | None) -> None:
    if NameValue and (NameValue not in Members or Members[NameValue].file_size):
        raise ValueError(
            "FreeCAD editable sketch has an additional or missing native shape"
        )


# the native wire cache independently corroborates every accepted local geometry edit
def CheckSketchFile(
    Archive: ZipFile,
    Members: Mapping[str, ZipInfo],
    Native: NativeObject,
    Original: Sketch,
    Edited: Sketch,
    Frame: Transform,
) -> None:
    ShapeFile, InternalFile = ReadSketchFiles(Native)
    CheckEmptyFile(Members, InternalFile)
    if not ShapeFile:
        if Original is not Edited:
            raise ValueError("FreeCAD editable sketch geometry edit has no saved shape")
        return
    ShapeData = ReadEditBrep(
        Archive, Members, ShapeFile, KMaxSketchBytes, "editable sketch"
    )
    if not IsSketchCache(ShapeData, Edited, Frame):
        raise ValueError(
            "FreeCAD editable sketch shape disagrees with its solved geometry"
        )


# standalone timeline carriers can never contribute their own saved shape
def CheckCarriers(
    Objects: Mapping[str, NativeObject], Members: Mapping[str, ZipInfo]
) -> None:
    for Native in Objects.values():
        if Native.type_id == "Part::Feature":
            CheckEmptyFile(Members, ReadPartEntry(Native.properties["Shape"]))
