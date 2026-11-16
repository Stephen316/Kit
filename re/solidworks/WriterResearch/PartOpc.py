"""The two package manifests for standalone SOLIDWORKS property parts."""

from collections.abc import Mapping
from xml.etree.ElementTree import Element, tostring

from PartFraming import VersionStorage
from PartManifests import KOffice, KPackage, KProperties, EncodeManifests
from convert.adapters.solidworks.Container.Format import (
    KContentTypesStream,
    KRelationshipsStream,
)


PACKAGE_NS = KPackage
OFFICE_NS = KOffice
APP_PROPERTIES, CORE_PROPERTIES, CUSTOM_PROPERTIES_XML = (Part[0] for Part in KProperties)


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
    for Path, _, _, _ in KProperties:
        if not Streams.get(Path):
            raise ValueError(f"the package relationship target is absent: {Path}")
    return EncodeManifests(Streams)
