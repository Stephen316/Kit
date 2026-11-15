from convert.formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.formats.Fusion.EntityCodec.Vocabulary.NativeCatalog import NativeCatalog


# pick schema must resolve unambiguously so entity identifiers retain their schema and reference meaning
def PickSchema(
    ClassGuid: str, Version: int | None, Catalog: NativeCatalog
) -> ClassSchema:
    Choices = tuple(
        Schema
        for Schema in Catalog.Classes.get(ClassGuid.upper(), ())
        if Version is None or Schema.SchemaVersion == Version
    )
    if Version is None and Choices:

        # ordering by schema schema version must stay deterministic so entity reconstruction resolves equivalent inputs consistently
        return max(Choices, key=lambda Schema: Schema.SchemaVersion)
    if len(Choices) != 1:
        raise ValueError("Unqualified Fusion native class or schema version")
    return Choices[0]
