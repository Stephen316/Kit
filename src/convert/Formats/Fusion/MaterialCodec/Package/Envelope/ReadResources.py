from convert.Formats.Fusion.MaterialCodec.Package.Model.ResourceInfo import ResourceInfo
from convert.Formats.Fusion.MaterialCodec.Package.Xml.CheckElement import CheckElement
from convert.Formats.Fusion.MaterialCodec.Package.Xml.ReadFields import ReadFields
from convert.Formats.Fusion.MaterialCodec.Package.Xml.ReadGroup import ReadGroup

# the resource types vocabulary must stay centralized so material reconstruction agrees on supported native identities
KResourceTypes = {
    "created": "time",
    "interop%20content": "bool",
    "name": "uri",
    "type": "string",
}


# the resources operation needs a distinct decoding boundary so typed appearance properties retain their native identifiers
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
