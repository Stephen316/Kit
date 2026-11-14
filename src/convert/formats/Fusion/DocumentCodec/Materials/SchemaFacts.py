from convert.formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode


def SchemaFacts(Declared: SchemaNode) -> tuple[str, str, bool]:
    TypeValue = ""
    LocalValue = ""
    Concrete = False
    for Child in Declared.Children:
        Attributes = dict(Child.Attributes)
        if Child.TagName == "type":
            TypeValue = Attributes["val"]
        if Child.TagName == "ui":
            Concrete = True
        if Attributes.get("id") == "localname":
            LocalValue = Attributes.get("val", "")
    return TypeValue, LocalValue, Concrete


def FindSchema(
    Indexed: dict[str, SchemaNode], TypeValue: str, LocalValue: str
) -> str | None:
    Found = tuple(
        NameValue
        for NameValue, Declared in Indexed.items()
        if SchemaFacts(Declared) == (TypeValue, LocalValue, True)
    )
    if len(Found) > 1:
        raise ValueError("Fusion material class names more than one schema")
    return Found[0] if Found else None
