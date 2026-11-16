# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Write the package manifests for ordinary SOLIDWORKS document properties."""

from collections.abc import Iterable
from io import BytesIO
from xml.sax.saxutils import XMLGenerator

KPackage = "http://schemas.openxmlformats.org/package/2006"
KOffice = "http://schemas.openxmlformats.org/officeDocument/2006"
KTypes = "[Content_Types].xml"
KRelations = "_rels/.rels"
KPackageMime = "application/vnd.openxmlformats-package"
KOfficeMime = "application/vnd.openxmlformats-officedocument"

# relationship order and slot identities come from the ordinary property inventory
KProperties = (
    ("docProps/app.xml", 3, KOffice, "extended-properties"),
    ("docProps/core.xml", 2, KPackage, "metadata/core-properties"),
    ("docProps/custom.xml", 4, KOffice, "custom-properties"),
)


# XMLGenerator emits escaped attribute data and self-closes the typed leaf records
def EncodeXml(Declaration, RootName, RootFields, Entries):
    Stream = BytesIO()
    Stream.write(Declaration.encode("ascii") + b"\r\n")
    Writer = XMLGenerator(Stream, encoding="utf-8", short_empty_elements=True)
    Writer.startElement(RootName, RootFields)
    for Name, Fields, Body in Entries:
        Writer.startElement(Name, Fields)
        if Body is not None:
            Writer.characters(Body)
        Writer.endElement(Name)
    Writer.endElement(RootName)
    Writer.endDocument()
    return Stream.getvalue() + b"\r\n"


# the referenced XML targets must belong to the same standalone part being assembled
def EncodeManifests(Members: Iterable[str]) -> dict[str, bytes]:
    Names = frozenset(Members)
    Missing = tuple(Name for Name, _, _, _ in KProperties if Name not in Names)
    if Missing:
        raise ValueError("package properties are missing: " + ", ".join(Missing))
    Types = (
        (
            "Default",
            {"Extension": "rels", "ContentType": KPackageMime + ".relationships+xml"},
        ),
        (
            "Default",
            {
                "Extension": "xml",
                "ContentType": KOfficeMime + ".extended-properties+xml",
            },
        ),
        (
            "Override",
            {
                "PartName": "/docProps/core.xml",
                "ContentType": KPackageMime + ".core-properties+xml",
            },
        ),
        (
            "Override",
            {
                "PartName": "/docProps/custom.xml",
                "ContentType": KOfficeMime + ".custom-properties+xml",
            },
        ),
    )
    Relationships = tuple(
        (
            "Relationship",
            {
                "Id": f"rId{Slot}",
                "Type": f"{Domain}/relationships/{Kind}",
                "Target": Name,
            },
        )
        for Name, Slot, Domain, Kind in KProperties
    )
    return {
        KTypes: EncodeXml(
            '<?xml version="1.0"?>',
            "Types",
            {"xmlns": KPackage + "/content-types"},
            ((Name, Fields, None) for Name, Fields in Types),
        ),
        KRelations: EncodeXml(
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            "Relationships",
            {"xmlns": KPackage + "/relationships"},
            ((Name, Fields, None) for Name, Fields in Relationships),
        ),
    }
