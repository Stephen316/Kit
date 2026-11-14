from collections.abc import Iterable
from xml.etree.ElementTree import Element as XmlElement

from convert.formats.Fusion.MaterialCodec.Package.Xml.TextElement import TextElement


def MakeFieldsMut(Parent: XmlElement, Fields: Iterable[tuple[str, str, str]]) -> None:
    for TagName, FieldName, TextValue in Fields:
        Parent.append(TextElement(TagName, {"name": FieldName}, TextValue))
