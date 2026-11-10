# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import dataclass as MakeDataClass
from xml.etree.ElementTree import Element

from convert.adapters.freecad.EditExtScope import EditSketchInput, ReadEditScope
from convert.adapters.freecad.EditRead.EditObjects import RequireEditObj
from convert.adapters.freecad.EditRead.EditProfile import CheckEditPlane
from convert.adapters.freecad.EditRead.OpenSketchXml import CheckOpenXml
from convert.adapters.freecad.EditRead.XmlField import CheckNoEditExpr, EditScalar
from convert.adapters.freecad.Native import EntryName, NativeObject
from interchange.document.models.DocumentModel import CadDocument
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.Transform import Transform

# these object families supply metadata and groups without independent geometry
KMetadataTypes = frozenset(
    {"App::DocumentObjectGroup", "App::FeaturePython", "Spreadsheet::Sheet"}
)


# native open sketch caches need their independent source geometry and frame for validation
@MakeDataClass(frozen=True, slots=True)
class OpenSketchCache:
    EntryName: str
    SketchValue: Sketch
    FrameValue: Transform


# native part caches retain element maps alongside the actual shape reference
def ReadPartEntry(Property: Element) -> str:
    Parts = Property.findall("./Part")
    if (
        Property.get("type") != "Part::PropertyPartShape"
        or len(Parts) != 1
        or any(
            Value.tag not in {"Part", "ElementMap", "ElementMap2"} for Value in Property
        )
    ):
        raise ValueError("FreeCAD editable extrusion has a malformed shape property")
    EntryValue = Parts[0].get("file", "")
    return EntryName(EntryValue) if EntryValue else ""


# approved shape fields exclude native geometry introduced outside the original sketch scope
def ReadEmptyParts(
    Objects: tuple[NativeObject, ...],
    AllowedNames: set[str],
    CacheFields: set[tuple[str, str]],
    Purpose: str = "editable extrusion",
) -> tuple[str, ...]:
    EmptyEntries: list[str] = []
    for ObjectValue in Objects:
        if (
            ObjectValue.name not in AllowedNames
            and ObjectValue.type_id not in KMetadataTypes
        ):
            raise ValueError(f"FreeCAD {Purpose} has an additional native object")
        for Field, Property in ObjectValue.properties.items():
            PropertyType = Property.get("type", "")
            if PropertyType.startswith("Mesh::"):
                raise ValueError(f"FreeCAD {Purpose} has additional mesh geometry")
            if (
                PropertyType != "Part::PropertyPartShape"
                or (ObjectValue.name, Field) in CacheFields
            ):
                continue
            if ShapeEntry := ReadPartEntry(Property):
                EmptyEntries.append(ShapeEntry)
    return tuple(EmptyEntries)


# independent sketch geometry and its timeline carrier must remain connected as authored
def CheckOpenParts(
    Carrier: NativeObject,
    Sketch: NativeObject,
    Plane: NativeObject,
    InputValue: EditSketchInput,
) -> None:
    if EditScalar(Carrier, "Profile", "App::PropertyLink", "Link") != Sketch.name:
        raise ValueError("FreeCAD independent sketch timeline link changed")
    CheckNoEditExpr(Carrier)
    CheckEditPlane(Sketch, Plane, InputValue.PlaneValue)
    CheckOpenXml(Sketch, InputValue.SketchValue)


# the original independent sketch inputs must still be attached to their own support frames
def ReadScopedParts(
    Objects: tuple[NativeObject, ...],
    Feature: NativeObject,
    DocValue: CadDocument,
    SketchId: str,
) -> tuple[str, tuple[str, ...], tuple[OpenSketchCache, ...]]:
    if not DocValue.feature_timeline:
        raise ValueError("FreeCAD editable extrusion is missing its source timeline")
    StepValue = DocValue.feature_timeline[-1]
    SketchInputs = ReadEditScope(DocValue, StepValue)
    if SketchInputs is None or SketchId != StepValue.sketch_id:
        raise ValueError(
            "FreeCAD editable extrusion has an invalid source sketch scope"
        )
    AllowedNames = {Feature.name}
    CacheFields = {(Feature.name, "Shape")}
    SketchEntry = ""
    OpenEntries: list[OpenSketchCache] = []
    for InputValue in SketchInputs:
        SourceSketch = InputValue.SketchValue
        SourcePlane = InputValue.PlaneValue
        Sketch = RequireEditObj(Objects, SourceSketch.id, "Sketcher::SketchObject")
        Plane = RequireEditObj(Objects, SourcePlane.id, "App::Plane")
        Carrier = RequireEditObj(Objects, InputValue.StepValue.id, "Part::Feature")
        AllowedNames.update((Sketch.name, Plane.name, Carrier.name))
        CacheFields.add((Sketch.name, "Shape"))
        Shape = Sketch.properties.get("Shape")
        ShapeEntry = ReadPartEntry(Shape) if Shape is not None else ""
        if SourceSketch.id == SketchId:
            SketchEntry = ShapeEntry
            continue
        CheckOpenParts(Carrier, Sketch, Plane, InputValue)
        if ShapeEntry:
            OpenEntries.append(
                OpenSketchCache(ShapeEntry, SourceSketch, SourcePlane.transform)
            )
    return (
        SketchEntry,
        ReadEmptyParts(Objects, AllowedNames, CacheFields),
        tuple(OpenEntries),
    )
