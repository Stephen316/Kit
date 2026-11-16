from pathlib import Path

from convert.Formats.Fusion.DocumentCodec.Vocabulary.NativeSchema import NativeSchema
from convert.Formats.Fusion.DocumentCodec.Vocabulary.ReadVocabulary import (
    ReadVocabulary,
)
from convert.Formats.Fusion.EntityCodec.Vocabulary.ReadCatalog import ReadCatalog

# direct guid must remain consistent across callers so model state retains its native feature and ownership relationships
KDirectGuid = "493A89BA-E146-498D-9033-2783FE727AF4"

# browser entry must remain consistent across callers so model state retains its native feature and ownership relationships
KBrowserEntry = "SubDSurfaceNodeBrowserEntry"


# direct schema needs an explicit validity boundary so model state retains its native feature and ownership relationships
def DirectSchema() -> NativeSchema:
    Versions = ReadCatalog().Classes.get(KDirectGuid, ())
    if len(Versions) != 1:
        raise ValueError("Fusion catalog lacks the Form direct-modeling data class")
    return NativeSchema("DirectModelingData", "Fusion", Versions[0])


# the author schemas contract needs a shared interpretation so model state retains its native feature and ownership relationships
def AuthorSchemas(
    ProfileKind: str,
    ConstrainRectangle: bool = False,
    HasFeatures: bool = False,
    HasPaste: bool = False,
) -> tuple[NativeSchema, ...]:
    Source = Path(__file__).parent
    Schemas = ReadVocabulary(Source / "DesignClasses.json")
    if ProfileKind == "form":
        Joined = {Schema.Value.ClassGuid.upper(): Schema for Schema in Schemas}
        for Schema in (*ReadVocabulary(Source / "FormClasses.json"), DirectSchema()):
            if Schema.NameValue != KBrowserEntry:
                Joined[Schema.Value.ClassGuid.upper()] = Schema
        return tuple(Joined.values())
    if ProfileKind not in ("rectangle", "cuboid", "part"):
        return Schemas
    Selected = {Schema.Value.ClassGuid.upper(): Schema for Schema in Schemas}
    for Schema in ReadVocabulary(Source / "RectangleClasses.json"):
        Selected[Schema.Value.ClassGuid.upper()] = Schema
    if HasFeatures:
        for Schema in ReadVocabulary(
            Source.parent / "PartFeatures" / "Vocabulary" / "FeatureClasses.json"
        ):
            Selected[Schema.Value.ClassGuid.upper()] = Schema
    if HasPaste:
        for Schema in ReadVocabulary(
            Source.parent / "PartFeatures" / "Vocabulary" / "PasteClasses.json"
        ):
            Selected[Schema.Value.ClassGuid.upper()] = Schema
    if ConstrainRectangle:
        for Schema in ReadVocabulary(
            Source.parent / "Rectangle" / "Dimensions" / "DimensionClasses.json"
        ):
            Selected[Schema.Value.ClassGuid.upper()] = Schema
    return tuple(Selected.values())
