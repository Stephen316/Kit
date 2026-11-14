from xml.etree.ElementTree import SubElement

from convert.formats.Fusion.MaterialCodec.Package.Xml.EmitPackageXml import (
    EmitPackageXml,
)
from convert.formats.Fusion.MaterialCodec.Package.Xml.MakeGroup import MakeGroup


def EmitLinks(Names: tuple[str, ...]) -> bytes:
    RootValue, Group = MakeGroup("default")
    for NameValue in Names:
        _ = SubElement(Group, "link", {"name": NameValue})
    return EmitPackageXml(RootValue)
