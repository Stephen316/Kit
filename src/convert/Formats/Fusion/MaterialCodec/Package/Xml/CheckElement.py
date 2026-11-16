from collections.abc import Mapping
from xml.etree.ElementTree import Element as XmlElement


# invalid element input must fail here so typed appearance properties retain their native identifiers
def CheckElement(
    Value: XmlElement,
    TagName: str,
    Attributes: Mapping[str, str],
    *,
    HasText: bool = False,
) -> None:
    if Value.tag != TagName or Value.attrib != dict(Attributes):
        raise ValueError("Unsupported material XML element shape")
    if not HasText and Value.text and Value.text.strip():
        raise ValueError("Unexpected material XML element text")
