from pathlib import Path

from convert.formats.Fusion.DocumentCodec.Vocabulary.NativeSchema import NativeSchema
from convert.formats.Fusion.DocumentCodec.Vocabulary.AuthorSchemas import AuthorSchemas
from convert.formats.Fusion.DocumentCodec.Vocabulary.ReadVocabulary import (
    ReadVocabulary,
)


def ReadNames() -> tuple[NativeSchema, ...]:
    RootPath = Path(__file__).parents[4] / "formats" / "Fusion"
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
