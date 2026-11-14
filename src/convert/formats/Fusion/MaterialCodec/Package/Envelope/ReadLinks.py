from convert.formats.Fusion.MaterialCodec.Package.Xml.CheckElement import CheckElement
from convert.formats.Fusion.MaterialCodec.Package.Xml.ReadGroup import ReadGroup


def ReadLinks(Payload: bytes) -> tuple[str, ...]:
    Group = ReadGroup(Payload, "default")
    Result: list[str] = []
    for Child in Group:
        NameValue = Child.attrib.get("name", "")
        CheckElement(Child, "link", {"name": NameValue})
        if len(Child) or not NameValue or NameValue in Result:
            raise ValueError("Invalid material package connection")
        Result.append(NameValue)
    return tuple(Result)
