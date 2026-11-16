from xml.etree.ElementTree import SubElement

from convert.Formats.Fusion.MaterialCodec.Package.Model.PackageCore import PackageCore
from convert.Formats.Fusion.MaterialCodec.Package.Xml.EmitPackageXml import (
    EmitPackageXml,
)
from convert.Formats.Fusion.MaterialCodec.Package.Xml.MakeFieldsMut import MakeFieldsMut
from convert.Formats.Fusion.MaterialCodec.Package.Xml.MakeGroup import MakeGroup


# the core operation needs a consistent construction rule so typed appearance properties retain their native identifiers
def EmitCore(Value: PackageCore) -> bytes:
    RootValue, Group = MakeGroup("content")
    Asset = SubElement(
        Group, "node", {"name": "asset", "class": "schema.autodesk.package.1.asset"}
    )
    Fields = [
        ("time", "created", Value.Created),
        ("uuid", "identifier", Value.Identifier),
    ]
    Optional = (
        ("uint32", "embed option", Value.EmbedOption),
        ("string", "name", Value.NameValue),
        ("string", "last saved", Value.LastSaved),
    )
    Fields.extend(
        (TagName, NameValue, str(Content))
        for TagName, NameValue, Content in Optional
        if Content is not None
    )
    if Value.IsReadOnly is not None:
        Fields.append(("bool", "read only", str(int(Value.IsReadOnly))))
    Fields.extend(
        (("time", "updated", Value.Updated), ("uint32", "updates", str(Value.Updates)))
    )
    MakeFieldsMut(Asset, Fields)
    return EmitPackageXml(RootValue)
