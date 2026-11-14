from struct import pack as PackValue
from typing import cast as CastValue

from convert.formats.Fusion.BundleCodec.Json.EmitJson import EmitJson
from convert.formats.Fusion.BundleCodec.Json.JsonTypes import KJsonValue
from convert.formats.Fusion.ContainerCodec.Model.DocProps import DocProps
from convert.formats.Fusion.ContainerCodec.Model.DocStruct import DocStruct


def StructTree(Value: DocStruct) -> dict[str, KJsonValue]:
    if (
        not isinstance(CastValue(object, Value), DocStruct)
        or any(
            type(TextValue) is not str or not TextValue
            for TextValue in (Value.Version, Value.TypeName, Value.Subtype)
        )
        or type(Value.Attributes) is not tuple
    ):
        raise ValueError("Invalid Fusion document structure properties")
    Attributes: dict[str, KJsonValue] = {}
    for Entry in Value.Attributes:
        PairValue = CastValue(tuple[object, ...], Entry)
        if (
            type(PairValue) is not tuple
            or len(PairValue) != 2
            or type(PairValue[0]) is not str
            or type(PairValue[1]) is not bool
            or not Entry[0]
            or Entry[0] in Attributes
        ):
            raise ValueError("Invalid Fusion document structure attribute")
        Attributes[Entry[0]] = Entry[1]
    return {
        "version": Value.Version,
        "type": Value.TypeName,
        "subtype": Value.Subtype,
        "attributes": Attributes,
    }


def EmitDocProps(Value: DocProps | None) -> bytes:
    if Value is None:
        return bytes(4)
    if not isinstance(CastValue(object, Value), DocProps):
        raise ValueError("Invalid Fusion document properties")
    TreeValue: dict[str, KJsonValue] = {}
    if Value.Structure is not None:
        TreeValue["docstruct"] = StructTree(Value.Structure)
    Payload = EmitJson(TreeValue)
    return PackValue("<I", len(Payload)) + Payload
