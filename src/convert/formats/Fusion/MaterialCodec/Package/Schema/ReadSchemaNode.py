from xml.etree.ElementTree import Element as XmlElement

from convert.formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode
from convert.formats.Fusion.MaterialCodec.Package.Xml.ParsePackageXml import (
    ParsePackageXml,
)


def NodeFromXml(Value: XmlElement) -> SchemaNode:
    return SchemaNode(
        Value.tag,
        tuple(Value.attrib.items()),
        tuple(NodeFromXml(Child) for Child in Value),
        (Value.text or "").strip(),
    )


def ReadSchemaNode(Payload: bytes) -> SchemaNode:
    return NodeFromXml(ParsePackageXml(Payload))
