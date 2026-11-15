from collections.abc import Mapping
from xml.etree.ElementTree import Element as XmlElement


# the text element contract needs a shared interpretation so typed appearance properties retain their native identifiers
def TextElement(
    TagName: str, Attributes: Mapping[str, str], TextValue: str
) -> XmlElement:
    Result = XmlElement(TagName, dict(Attributes))
    setattr(Result, "text", TextValue)
    return Result
