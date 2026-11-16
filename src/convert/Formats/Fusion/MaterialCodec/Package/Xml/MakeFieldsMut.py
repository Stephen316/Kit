from collections.abc import Iterable
from xml.etree.ElementTree import Element as XmlElement

from convert.Formats.Fusion.MaterialCodec.Package.Xml.TextElement import TextElement


# the fields operation needs a consistent construction rule so typed appearance properties retain their native identifiers
def MakeFieldsMut(Parent: XmlElement, Fields: Iterable[tuple[str, str, str]]) -> None:
    for TagName, FieldName, TextValue in Fields:
        Parent.append(TextElement(TagName, {"name": FieldName}, TextValue))
