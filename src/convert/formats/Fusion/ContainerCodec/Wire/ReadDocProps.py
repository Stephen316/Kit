from struct import unpack_from as UnpackFrom

from convert.formats.Fusion.BundleCodec.Json.ReadJson import ReadJson
from convert.formats.Fusion.ContainerCodec.Model.DocProps import DocProps
from convert.formats.Fusion.ContainerCodec.Model.DocStruct import DocStruct
from convert.formats.Fusion.ContainerCodec.Wire.EmitDocProps import EmitDocProps

KStructKeys = ("version", "type", "subtype", "attributes")


def ReadDocProps(Payload: bytes) -> DocProps | None:
    if len(Payload) < 4 or UnpackFrom("<I", Payload)[0] != len(Payload) - 4:
        raise ValueError("Invalid Fusion document properties length")
    if len(Payload) == 4:
        return None
    TreeValue = ReadJson(Payload[4:])
    if not isinstance(TreeValue, dict) or set(TreeValue) - {"docstruct"}:
        raise ValueError("Unsupported Fusion document properties")
    Structure: DocStruct | None = None
    Inner = TreeValue.get("docstruct")
    if Inner is not None:
        if not isinstance(Inner, dict) or tuple(Inner) != KStructKeys:
            raise ValueError("Unsupported Fusion document structure properties")
        Version, TypeName, Subtype = Inner["version"], Inner["type"], Inner["subtype"]
        Attributes = Inner["attributes"]
        if (
            not isinstance(Version, str)
            or not isinstance(TypeName, str)
            or not isinstance(Subtype, str)
            or not isinstance(Attributes, dict)
            or any(type(FlagValue) is not bool for FlagValue in Attributes.values())
        ):
            raise ValueError("Unsupported Fusion document structure properties")
        Structure = DocStruct(
            Version,
            TypeName,
            Subtype,
            tuple((KeyName, FlagValue is True) for KeyName, FlagValue in Attributes.items()),
        )
    Result = DocProps(Structure)
    if EmitDocProps(Result) != Payload:
        raise ValueError("Unsupported Fusion document properties encoding")
    return Result
