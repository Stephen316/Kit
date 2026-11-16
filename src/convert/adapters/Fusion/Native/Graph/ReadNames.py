from pathlib import Path

from convert.Formats.Fusion.DocumentCodec.Vocabulary.NativeSchema import NativeSchema
from convert.Formats.Fusion.DocumentCodec.Vocabulary.AuthorSchemas import AuthorSchemas
from convert.Formats.Fusion.DocumentCodec.Vocabulary.ReadVocabulary import (
    ReadVocabulary,
)


# the names operation needs a distinct decoding boundary so public document claims remain grounded in native records
def ReadNames() -> tuple[NativeSchema, ...]:
    RootPath = Path(__file__).parents[4] / "Formats" / "Fusion"
    Paths = (
        RootPath / "DocumentCodec/Vocabulary/DesignClasses.json",
        RootPath / "ContainerCodec/Assembly/ActClasses.json",
        RootPath / "ContainerCodec/Browser/BrowserClasses.json",
    )
    Catalog = {
        Schema.Value.ClassGuid.upper(): Schema
        for Schema in AuthorSchemas("cuboid", True)
    }
    for Source in Paths:
        for Schema in ReadVocabulary(Source):
            Catalog[Schema.Value.ClassGuid.upper()] = Schema
    return tuple(Catalog.values())
