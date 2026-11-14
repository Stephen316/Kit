from convert.formats.Fusion.MaterialCodec.Models.PropertySpec import PropertySpec
from convert.formats.Fusion.MaterialCodec.Wire.EncodeText import EncodeText


def CheckProperty(Field: PropertySpec) -> None:
    if not Field.FieldName or not EncodeText(Field.FieldName):
        raise ValueError("Fusion material property requires an identifier")
    if Field.ValueKind not in (
        "String",
        "URL",
        "Uuid",
        "Integer",
        "Choice",
        "Boolean",
        "Float",
        "Color",
        "Reference",
        "TextureURI",
        "ui",
        "implementation",
    ):
        raise ValueError("Unsupported Fusion material property type")
    if Field.ValueKind in ("ui", "implementation") and (
        not Field.IsReadOnly or Field.IsDefinition
    ):
        raise ValueError("Fusion material schema metadata must be read-only")
    if any(
        type(Value) is not bool
        for Value in (Field.IsDefinition, Field.IsReadOnly, Field.IsMultiple)
    ):
        raise ValueError("Fusion material schema flags must be booleans")
    if Field.ConnectMode not in ("none", "single", "multiple"):
        raise ValueError("Unsupported Fusion material connection mode")
    if Field.UnitName is not None:
        if Field.ValueKind != "Float" or not Field.UnitName:
            raise ValueError("Only Fusion material floats can declare units")
        _ = EncodeText(Field.UnitName)
    if Field.IsMultiple and Field.ValueKind not in (
        "String",
        "URL",
        "Uuid",
        "Float",
        "TextureURI",
    ):
        raise ValueError("Only material text and number lists have wire evidence")
    if Field.IsDefinition and Field.ConnectMode != "none":
        raise ValueError("Material definition connections are unsupported")
    if Field.ValueKind == "Reference" and Field.ConnectMode == "none":
        raise ValueError("Fusion material references require a connection mode")
