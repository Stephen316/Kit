from xml.etree.ElementTree import SubElement

from convert.formats.Fusion.MaterialCodec.Package.Model.ResourceInfo import ResourceInfo
from convert.formats.Fusion.MaterialCodec.Package.Xml.EmitPackageXml import (
    EmitPackageXml,
)
from convert.formats.Fusion.MaterialCodec.Package.Xml.MakeFieldsMut import MakeFieldsMut
from convert.formats.Fusion.MaterialCodec.Package.Xml.MakeGroup import MakeGroup


def EmitResources(Values: tuple[ResourceInfo, ...]) -> bytes:
    RootValue, Group = MakeGroup("default")
    for Value in Values:
        Child = SubElement(
            Group,
            "link",
            {"name": Value.LinkName, "class": "schema.autodesk.data.1.resource"},
        )
        MakeFieldsMut(
            Child,
            (
                ("time", "created", Value.Created),
                ("bool", "interop%20content", str(int(Value.IsInterop))),
                ("uri", "name", Value.FileName),
                ("string", "type", Value.ContentType),
            ),
        )
    return EmitPackageXml(RootValue)
