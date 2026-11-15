from xml.etree.ElementTree import Element as XmlElement

from convert.formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode
from convert.formats.Fusion.MaterialCodec.Package.Xml.ParsePackageXml import (
    ParsePackageXml,
)


# the node from xml contract needs a shared interpretation so typed appearance properties retain their native identifiers
def NodeFromXml(Value: XmlElement) -> SchemaNode:
    return SchemaNode(
        Value.tag,
        tuple(Value.attrib.items()),
        tuple(NodeFromXml(Child) for Child in Value),
        (Value.text or "").strip(),
    )


# the schema node operation needs a distinct decoding boundary so typed appearance properties retain their native identifiers
def ReadSchemaNode(Payload: bytes) -> SchemaNode:
    return NodeFromXml(ParsePackageXml(Payload))
