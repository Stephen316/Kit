from convert.formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode
from convert.formats.Fusion.MaterialCodec.Package.Schema.SchemaGrammar import (
    KSchemaAttrs,
    KSchemaChildren,
)


def CheckNode(Value: SchemaNode) -> None:
    if Value.TagName not in KSchemaAttrs or Value.TextValue:
        raise ValueError("Unsupported material schema declaration")
    Attributes = dict(Value.Attributes)
    if len(Attributes) != len(Value.Attributes) or set(Attributes) - set(
        KSchemaAttrs[Value.TagName]
    ):
        raise ValueError("Unsupported or duplicate material schema attributes")
    if any(
        type(NameValue) is not str
        or type(TextValue) is not str
        or len(TextValue) > 65536
        for NameValue, TextValue in Value.Attributes
    ):
        raise ValueError("Invalid material schema attribute text")
    Allowed = KSchemaChildren.get(Value.TagName, ())
    if any(Child.TagName not in Allowed for Child in Value.Children):
        raise ValueError("Unsupported material schema child")
    if Value.TagName in ("UID", "Base", "type") and set(Attributes) != {"val"}:
        raise ValueError("Material schema reference requires a value")
    if Value.TagName not in (
        "UID",
        "Base",
        "type",
        "Bounds",
        "AssetSchema",
    ) and not Attributes.get("id"):
        raise ValueError("Material schema property requires an identity")
    for NameValue in (
        "readonly",
        "public",
        "local",
        "metadata",
        "definitionIteratorData",
        "allowmultiplevalues",
    ):
        if NameValue in Attributes and Attributes[NameValue] not in ("true", "false"):
            raise ValueError("Invalid material schema boolean attribute")
