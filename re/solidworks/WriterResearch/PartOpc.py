"""The two package manifests for standalone SOLIDWORKS property parts."""

from collections.abc import Mapping
from dataclasses import dataclass
from xml.etree.ElementTree import Element, SubElement, tostring

from PartFraming import VersionStorage
from convert.adapters.solidworks.Container.Format import (
    KContentTypesStream,
    KRelationshipsStream,
)


PACKAGE_NS = "http://schemas.openxmlformats.org/package/2006"
OFFICE_NS = "http://schemas.openxmlformats.org/officeDocument/2006"
PACKAGE_MIME = "application/vnd.openxmlformats-package."
OFFICE_MIME = "application/vnd.openxmlformats-officedocument."
APP_PROPERTIES = "docProps/app.xml"
CORE_PROPERTIES = "docProps/core.xml"
CUSTOM_PROPERTIES_XML = "docProps/custom.xml"


@dataclass(frozen=True)
class PropertyPart:
    Path: str
    RelationshipId: str
    RelationshipType: str
    ContentType: str


EXTENDED = PropertyPart(
    APP_PROPERTIES,
    "rId3",
    f"{OFFICE_NS}/relationships/extended-properties",
    f"{OFFICE_MIME}extended-properties+xml",
)
CORE = PropertyPart(
    CORE_PROPERTIES,
    "rId2",
    f"{PACKAGE_NS}/relationships/metadata/core-properties",
    f"{PACKAGE_MIME}core-properties+xml",
)
CUSTOM = PropertyPart(
    CUSTOM_PROPERTIES_XML,
    "rId4",
    f"{OFFICE_NS}/relationships/custom-properties",
    f"{OFFICE_MIME}custom-properties+xml",
)


# Native MSXML emits compact empty elements and a final carriage return and newline.
def EncodePackageXml(Root: Element, *, Standalone: bool) -> bytes:
    Declaration = '<?xml version="1.0"'
    if Standalone:
        Declaration += ' encoding="UTF-8" standalone="yes"'
    Body: bytes = tostring(Root, encoding="utf-8")
    return (Declaration + "?>\r\n").encode("ascii") + Body.replace(b" />", b"/>") + b"\r\n"


# Resolve every relationship against the exact canonical emitted stream path.
def EncodePartOpc(Generation: int, Streams: Mapping[str, bytes]) -> dict[str, bytes]:
    VersionStorage(Generation)
    if KContentTypesStream in Streams or KRelationshipsStream in Streams:
        raise ValueError("the package constructor owns both manifest streams")
    Parts = (EXTENDED, CORE, CUSTOM)
    for Part in Parts:
        if not Streams.get(Part.Path):
            raise ValueError(f"the package relationship target is absent: {Part.Path}")

    Relationships = Element("Relationships", xmlns=f"{PACKAGE_NS}/relationships")
    for Part in Parts:
        _ = SubElement(
            Relationships,
            "Relationship",
            Id=Part.RelationshipId,
            Type=Part.RelationshipType,
            Target=Part.Path,
        )

    Types = Element("Types", xmlns=f"{PACKAGE_NS}/content-types")
    _ = SubElement(
        Types,
        "Default",
        Extension="rels",
        ContentType=f"{PACKAGE_MIME}relationships+xml",
    )
    _ = SubElement(Types, "Default", Extension="xml", ContentType=EXTENDED.ContentType)
    for Part in (CORE, CUSTOM):
        _ = SubElement(Types, "Override", PartName=f"/{Part.Path}", ContentType=Part.ContentType)
    return {
        KContentTypesStream: EncodePackageXml(Types, Standalone=False),
        KRelationshipsStream: EncodePackageXml(Relationships, Standalone=True),
    }
