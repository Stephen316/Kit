from convert.formats.Fusion.MaterialCodec.Package.Model.ResourceInfo import ResourceInfo
from convert.formats.Fusion.MaterialCodec.Package.Xml.CheckElement import CheckElement
from convert.formats.Fusion.MaterialCodec.Package.Xml.ReadFields import ReadFields
from convert.formats.Fusion.MaterialCodec.Package.Xml.ReadGroup import ReadGroup

KResourceTypes = {
    "created": "time",
    "interop%20content": "bool",
    "name": "uri",
    "type": "string",
}


def ReadResources(Payload: bytes) -> tuple[ResourceInfo, ...]:
    Group = ReadGroup(Payload, "default")
    Result: list[ResourceInfo] = []
    for Child in Group:
        NameValue = Child.attrib.get("name", "")
        CheckElement(
            Child,
            "link",
            {"name": NameValue, "class": "schema.autodesk.data.1.resource"},
        )
        Fields = ReadFields(Child, KResourceTypes)
        if Fields.keys() != KResourceTypes.keys() or Fields[
            "interop%20content"
        ] not in ("0", "1"):
            raise ValueError("Unsupported material resource metadata")
        Result.append(
            ResourceInfo(
                NameValue,
                Fields["name"],
                Fields["type"],
                Fields["created"],
                Fields["interop%20content"] == "1",
            )
        )
    return tuple(Result)
