from xml.etree.ElementTree import Element as XmlElement

from convert.formats.Fusion.MaterialCodec.Package.Xml.CheckElement import CheckElement
from convert.formats.Fusion.MaterialCodec.Package.Xml.ParsePackageXml import (
    ParsePackageXml,
)


# the group operation needs a distinct decoding boundary so typed appearance properties retain their native identifiers
def ReadGroup(Payload: bytes, GroupName: str) -> XmlElement:
    RootValue = ParsePackageXml(Payload)
    CheckElement(RootValue, "root", {"version": "1", "name": "root"})
    if len(RootValue) != 1:
        raise ValueError("Material XML requires one group")
    CheckElement(RootValue[0], "group", {"name": GroupName})
    return RootValue[0]
