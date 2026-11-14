from collections.abc import Mapping
from xml.etree.ElementTree import Element as XmlElement


def TextElement(
    TagName: str, Attributes: Mapping[str, str], TextValue: str
) -> XmlElement:
    Result = XmlElement(TagName, dict(Attributes))
    setattr(Result, "text", TextValue)
    return Result
