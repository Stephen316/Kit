from convert.formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.formats.Fusion.EntityCodec.Vocabulary.NativeCatalog import NativeCatalog


def PickSchema(
    ClassGuid: str, Version: int | None, Catalog: NativeCatalog
) -> ClassSchema:
    Choices = tuple(
        Schema
        for Schema in Catalog.Classes.get(ClassGuid.upper(), ())
        if Version is None or Schema.SchemaVersion == Version
    )
    if Version is None and Choices:
        return max(Choices, key=lambda Schema: Schema.SchemaVersion)
    if len(Choices) != 1:
        raise ValueError("Unqualified Fusion native class or schema version")
    return Choices[0]
