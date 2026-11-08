# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from xml.etree.ElementTree import Element

from convert.adapters.freecad.EditRead.EditObjects import RequireEditObj
from convert.adapters.freecad.Native import EntryName, NativeObject
from interchange.document.models.DocumentModel import CadDocument

# these object families supply metadata and groups without independent geometry
KMetadataTypes = frozenset(
    {"App::DocumentObjectGroup", "App::FeaturePython", "Spreadsheet::Sheet"}
)


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


# extra native geometry cannot be represented by the original single body snapshot
def ReadEditParts(
    Objects: tuple[NativeObject, ...], Feature: NativeObject, DocValue: CadDocument
) -> tuple[str, tuple[str, ...]]:
    Sketch = RequireEditObj(Objects, DocValue.sketches[0].id, "Sketcher::SketchObject")
    Plane = RequireEditObj(Objects, DocValue.support_planes[0].id, "App::Plane")
    Carrier = RequireEditObj(Objects, DocValue.feature_timeline[0].id, "Part::Feature")
    AllowedNames = {Feature.name, Sketch.name, Plane.name, Carrier.name}
    CacheFields = {(Feature.name, "Shape"), (Sketch.name, "Shape")}
    SketchEntry = (
        ReadPartEntry(Sketch.properties["Shape"])
        if "Shape" in Sketch.properties
        else ""
    )
    EmptyEntries: list[str] = []
    for ObjectValue in Objects:
        if (
            ObjectValue.name not in AllowedNames
            and ObjectValue.type_id not in KMetadataTypes
        ):
            raise ValueError(
                "FreeCAD editable extrusion has an additional native object"
            )
        for Field, Property in ObjectValue.properties.items():
            PropertyType = Property.get("type", "")
            if PropertyType.startswith("Mesh::"):
                raise ValueError(
                    "FreeCAD editable extrusion has additional mesh geometry"
                )
            if (
                PropertyType != "Part::PropertyPartShape"
                or (ObjectValue.name, Field) in CacheFields
            ):
                continue
            if ShapeEntry := ReadPartEntry(Property):
                EmptyEntries.append(ShapeEntry)
    return SketchEntry, tuple(EmptyEntries)
