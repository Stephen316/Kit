from convert.formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode


def SchemaFields(
    NameValue: str,
    Schemas: dict[str, SchemaNode],
    Ancestry: tuple[str, ...] = (),
) -> dict[str, SchemaNode]:
    if NameValue in Ancestry or NameValue not in Schemas:
        raise ValueError("Invalid authored material schema ancestry")
    Fields: dict[str, SchemaNode] = {}
    for Child in Schemas[NameValue].Children:
        Attributes = dict(Child.Attributes)
        if Child.TagName == "Base":
            Fields.update(
                SchemaFields(Attributes["val"], Schemas, (*Ancestry, NameValue))
            )
        if "id" in Attributes and Child.TagName != "PropertyAlias":
            Fields[Attributes["id"]] = Child
    return Fields
