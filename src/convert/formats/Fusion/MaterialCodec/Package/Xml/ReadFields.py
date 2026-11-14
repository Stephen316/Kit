from collections.abc import Mapping
from xml.etree.ElementTree import Element as XmlElement


def ReadFields(Value: XmlElement, Types: Mapping[str, str]) -> dict[str, str]:
    Fields: dict[str, str] = {}
    for Child in Value:
        FieldName = Child.attrib.get("name", "")
        if (
            FieldName in Fields
            or Types.get(FieldName) != Child.tag
            or Child.attrib != {"name": FieldName}
            or len(Child)
        ):
            raise ValueError("Unsupported or duplicate material XML field")
        Fields[FieldName] = Child.text or ""
    return Fields
