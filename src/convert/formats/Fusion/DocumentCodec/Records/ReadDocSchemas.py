from pathlib import Path
from convert.formats.Fusion.DocumentCodec.Records.NativeAuxiliary import (
    KAuxiliarySchemas,
)

from convert.formats.Fusion.DocumentCodec.Vocabulary.ReadVocabulary import (
    ReadVocabulary,
)
from convert.formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema


def ReadDocSchemas() -> tuple[ClassSchema, ...]:
    FusionPath = Path(__file__).parents[2]
    Paths = (
        FusionPath / "DocumentCodec" / "Vocabulary" / "DesignClasses.json",
        FusionPath / "DocumentCodec" / "Vocabulary" / "FormClasses.json",
        FusionPath / "DocumentCodec" / "Vocabulary" / "SavedClasses.json",
        FusionPath / "ContainerCodec" / "Assembly" / "ActClasses.json",
        FusionPath / "ContainerCodec" / "Browser" / "BrowserClasses.json",
        FusionPath
        / "DocumentCodec"
        / "PartFeatures"
        / "Vocabulary"
        / "PasteClasses.json",
        FusionPath / "DocumentCodec" / "Vocabulary" / "HistoricClasses.json",
    )
    Catalog: dict[tuple[str, int], ClassSchema] = {}
    for Source in Paths:
        for Schema in ReadVocabulary(Source):
            KeyValue = (Schema.Value.ClassGuid.upper(), Schema.Value.SchemaVersion)
            Previous = Catalog.get(KeyValue)
            if Previous is not None and Previous != Schema.Value:
                raise ValueError("Conflicting native schema vocabulary")
            Catalog[KeyValue] = Schema.Value
    return tuple(Catalog.values()) + KAuxiliarySchemas
