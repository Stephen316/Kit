from xml.etree.ElementTree import Element as XmlElement
from xml.etree.ElementTree import ParseError, fromstring as ParseXml  # noqa: DUO107

from convert.formats.Fusion.MaterialCodec.Package.PackageLimits import (
    KMaxXmlBytes,
    KMaxXmlDepth,
    KMaxSchemaNodes,
)


def ParsePackageXml(Payload: bytes) -> XmlElement:
    if not 0 < len(Payload) <= KMaxXmlBytes:
        raise ValueError("Invalid material XML size")
    try:
        Content = Payload.decode("utf-8")
        WithoutHeader = (
            Content.split("?>", 1)[1] if Content.startswith("<?xml ") else Content
        )
        if "<!" in Content or "<?" in WithoutHeader:
            raise ValueError(
                "Material XML declarations and processing instructions are unsupported"
            )
        RootValue = ParseXml(Content)
    except (UnicodeError, ParseError) as ErrorInfo:
        raise ValueError("Invalid material XML") from ErrorInfo
    Pending, Count = [(RootValue, 0)], 0
    while Pending:
        Value, Depth = Pending.pop()
        Count += 1
        if Count > KMaxSchemaNodes or Depth > KMaxXmlDepth:
            raise ValueError("Material XML exceeds structure limits")
        if Value.tail and Value.tail.strip():
            raise ValueError("Material XML mixed content is unsupported")
        Pending.extend((Child, Depth + 1) for Child in Value)
    return RootValue
