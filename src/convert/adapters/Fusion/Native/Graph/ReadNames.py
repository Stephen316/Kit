from pathlib import Path

from convert.Formats.Fusion.DocumentCodec.Auxiliary.Mesh.MeshLayout import (
    KMeshGroupGuid,
    KTextureGuid,
)
from convert.Formats.Fusion.EntityCodec.Vocabulary.ReadCatalog import ReadCatalog

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
    MeshClasses = ReadCatalog().Classes
    for ClassName, GuidValue in (
        ("ParaMeshBodies", KMeshGroupGuid),
        ("ParaMeshTextureStore", KTextureGuid),
    ):
        Versions = MeshClasses.get(GuidValue, ())
        if len(Versions) != 1 or Versions[0].SchemaVersion != 0:
            raise ValueError(
                "Fusion catalog lacks the original empty mesh scaffold classes"
            )
        Catalog[GuidValue] = NativeSchema(ClassName, "Fusion", Versions[0])
    return tuple(Catalog.values())
