from re import fullmatch as FullMatch

from convert.formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode


def SchemaIdentity(Value: SchemaNode) -> str:
    Identities = [
        dict(Child.Attributes).get("val", "")
        for Child in Value.Children
        if Child.TagName == "UID"
    ]
    if (
        len(Identities) != 1
        or FullMatch(r"[A-Za-z][A-Za-z0-9]{0,127}", Identities[0]) is None
    ):
        raise ValueError("Invalid material schema UID")
    return Identities[0]
