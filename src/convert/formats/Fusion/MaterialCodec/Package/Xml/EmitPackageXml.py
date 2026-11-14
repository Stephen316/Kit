from xml.etree.ElementTree import Element as XmlElement
from xml.etree.ElementTree import tostring as EmitXml  # noqa: DUO107

from convert.formats.Fusion.MaterialCodec.Package.PackageLimits import KMaxXmlBytes


def EmitPackageXml(Value: XmlElement) -> bytes:
    Payload: bytes = EmitXml(Value, encoding="utf-8", xml_declaration=True)
    if len(Payload) > KMaxXmlBytes:
        raise ValueError("Material XML exceeds size limit")
    return Payload
