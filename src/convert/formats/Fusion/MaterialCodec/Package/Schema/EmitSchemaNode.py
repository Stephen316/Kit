from xml.etree.ElementTree import Element as XmlElement

from convert.formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode
from convert.formats.Fusion.MaterialCodec.Package.Xml.EmitPackageXml import (
    EmitPackageXml,
)
from convert.formats.Fusion.MaterialCodec.Package.Xml.TextElement import TextElement


# the xml from node contract needs a shared interpretation so typed appearance properties retain their native identifiers
def XmlFromNode(Value: SchemaNode) -> XmlElement:
    Result = TextElement(Value.TagName, dict(Value.Attributes), Value.TextValue)
    Result.extend(XmlFromNode(Child) for Child in Value.Children)
    return Result


# the schema node operation needs a consistent construction rule so typed appearance properties retain their native identifiers
def EmitSchemaNode(Value: SchemaNode) -> bytes:
    return EmitPackageXml(XmlFromNode(Value))
