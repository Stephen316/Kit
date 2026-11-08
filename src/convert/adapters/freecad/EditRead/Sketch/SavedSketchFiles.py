# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.adapters.freecad.Native import EntryName, NativeObject


# optional saved part streams are explicit references inside the validated archive
def ReadShapeFile(Native: NativeObject, NameValue: str) -> str | None:
    Property = Native.properties.get(NameValue)
    if (
        Property is None
        or Property.get("type") != "Part::PropertyPartShape"
        or not len(Property)
        or Property[0].tag != "Part"
        or len(Property[0])
    ):
        raise ValueError("FreeCAD saved sketch shape property changed")
    PartValue = Property[0]
    FileName = PartValue.get("file")
    if FileName is None:
        if PartValue.attrib or len(Property) != 1:
            raise ValueError("FreeCAD saved sketch has an unbound shape cache")
        return None
    Metadata = tuple(NodeValue.tag for NodeValue in Property[1:])
    if PartValue.attrib.keys() - {
        "file",
        "ElementMap",
        "HasherIndex",
    } or Metadata not in ((), ("ElementMap",), ("ElementMap", "ElementMap2")):
        raise ValueError("FreeCAD saved sketch shape metadata changed")
    if not FileName.endswith(".brp"):
        raise ValueError("FreeCAD saved sketch shape cache has the wrong format")
    return EntryName(FileName)


# separate shape properties prevent internal topology from being read as the sketch wire
def ReadSketchFiles(Native: NativeObject) -> tuple[str | None, str | None]:
    Shape = ReadShapeFile(Native, "Shape")
    Internal = ReadShapeFile(Native, "InternalShape")
    if Shape is not None and Shape == Internal:
        raise ValueError("FreeCAD saved sketch shape caches are ambiguous")
    return Shape, Internal
