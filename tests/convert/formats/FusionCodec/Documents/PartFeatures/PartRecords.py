from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.Vocabulary.ReadVocabulary import (
    ReadVocabulary,
)
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from tests.convert.formats.FusionCodec.Documents.PartFeatures.PartCases import (
    KRepoRoot,
)

# the vocabularies cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KVocabularies = (
    "src/convert/formats/Fusion/DocumentCodec/Vocabulary/DesignClasses.json",
    "src/convert/formats/Fusion/DocumentCodec/PartFeatures/Vocabulary/FeatureClasses.json",
    "src/convert/formats/Fusion/DocumentCodec/PartFeatures/Vocabulary/PasteClasses.json",
)


# shared class guids setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def ClassGuids() -> dict[str, str]:
    return {
        Schema.NameValue: Schema.Value.ClassGuid.upper()
        for Source in KVocabularies
        for Schema in ReadVocabulary(KRepoRoot / Source)
    }


# shared part records setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def PartRecords(
    Model: DocumentModel, ClassName: str
) -> tuple[dict[str, KEntityValue], ...]:
    Identity = ClassGuids()[ClassName]
    return tuple(
        {
            FieldValue.FieldName: FieldValue.Value
            for Group in Record.Groups
            for FieldValue in Group.Fields
        }
        for Segment in Model.Segments
        if Segment.Metadata.Header.SegmentId == 0
        for Record in Segment.Records
        if Record.Groups[0].ClassGuid.upper() == Identity
    )
