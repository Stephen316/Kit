# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from xml.etree.ElementTree import Element


# only the documented tree framing can describe the native model objects
def CheckGraphTree(Document: Element) -> None:
    Tags = tuple(Value.tag for Value in Document)
    if (
        Document.tag != "Document"
        or Document.get("SchemaVersion") != "4"
        or Document.get("FileVersion") != "1"
        or Tags
        not in (
            ("Properties", "Objects", "ObjectData"),
            ("StringHasher", "StringHasher2", "Properties", "Objects", "ObjectData"),
        )
    ):
        raise ValueError("FreeCAD editable Scale native document framing changed")
    Objects = Document[-2]
    ObjectData = Document[-1]
    if (
        set(Objects.attrib) != {"Count", "Dependencies"}
        or Objects.get("Dependencies") != "1"
        or set(ObjectData.attrib) != {"Count"}
    ):
        raise ValueError("FreeCAD editable Scale native object framing changed")
    DeclareNames = set()
    DepNames = set()
    for Value in Objects:
        if Value.tag == "Object":
            NameValue = Value.get("name", "")
            if (
                len(Value)
                or not Value.get("id")
                or set(Value.attrib) - {"name", "type", "id", "Touched"}
                or Value.get("Touched", "1") != "1"
            ):
                raise ValueError("FreeCAD editable Scale native rebuild is invalid")
            DeclareNames.add(NameValue)
        elif Value.tag == "ObjectDeps" and Value.attrib.keys() == {"Name", "Count"}:
            if any(
                Link.tag != "Dep" or len(Link) or Link.attrib.keys() != {"Name"}
                for Link in Value
            ):
                raise ValueError("FreeCAD editable Scale native dependency row changed")
            DepNames.add(Value.get("Name"))
        else:
            raise ValueError("FreeCAD editable Scale native dependency framing changed")
    if DeclareNames != DepNames:
        raise ValueError("FreeCAD editable Scale native dependencies are incomplete")
    for Value in ObjectData:
        CheckDataNode(Value)


# object properties and extensions must have one unambiguous native container
def CheckDataNode(Value: Element) -> None:
    Tags = tuple(Child.tag for Child in Value)
    WithExt = Tags == ("Extensions", "Properties")
    Attrs = {"name", "Extensions"} if WithExt else {"name"}
    if (
        Value.tag != "Object"
        or Tags not in (("Properties",), ("Extensions", "Properties"))
        or set(Value.attrib) != Attrs
        or (WithExt and Value.get("Extensions") != "True")
    ):
        raise ValueError("FreeCAD editable Scale native object data changed")
    if WithExt:
        Extensions = Value[0]
        if (
            Extensions.attrib != {"Count": str(len(Extensions))}
            or len(Extensions) != 1
            or Extensions[0].tag != "Extension"
        ):
            raise ValueError("FreeCAD editable Scale native extension framing changed")
    Properties = Value[-1]
    if set(Properties.attrib) != {"Count", "TransientCount"} or any(
        Child.tag not in ("Property", "_Property") for Child in Properties
    ):
        raise ValueError("FreeCAD editable Scale native property framing changed")
