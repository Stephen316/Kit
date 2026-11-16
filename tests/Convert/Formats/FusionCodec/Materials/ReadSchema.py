from typing import cast as CastValue
from xml.etree.ElementTree import Element as XmlElement

from convert.Formats.Fusion.MaterialCodec.Models.MaterialSchema import MaterialSchema
from convert.Formats.Fusion.MaterialCodec.Models.PropertySpec import (
    KConnectMode,
    KPropertyKind,
    PropertySpec,
)


# shared read schema setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def ReadSchema(Schema: XmlElement) -> MaterialSchema:
    Identity = Schema.find("UID")
    assert Identity is not None
    Properties = tuple(
        PropertySpec(
            Field.attrib["id"],
            CastValue(KPropertyKind, Field.tag),
            Field.attrib.get("definitionIteratorData") == "true",
            Field.attrib.get("readonly") == "true",
            Field.attrib.get("allowmultiplevalues") == "true",
            Field.attrib.get("unit"),
            CastValue(KConnectMode, Field.attrib.get("allowconnectedassets", "none")),
        )
        for Field in Schema
        if "id" in Field.attrib
    )
    return MaterialSchema(
        Identity.attrib["val"],
        tuple(BaseNode.attrib["val"] for BaseNode in Schema.findall("Base")),
        Properties,
    )
