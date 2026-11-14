from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.LinkAuthor.Records.LinkGuids import (
    KAssetRecipe,
    KDataRef,
    KOccurRecipe,
    KRecipe,
)
from convert.formats.Fusion.LinkAuthor.Records.PathValues import OccurActRef
from convert.formats.Fusion.LinkAuthor.Records.RecordValues import (
    LocalSeries,
    MakeGroup,
    MakeMatrix,
    MakeRecord,
)
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


@MakeDataClass(frozen=True, slots=True)
class OccurRef:
    Identities: tuple[int, int, int]
    ReferenceKind: int
    Cached: int
    Matrix: tuple[float, ...] | None
    Parent: int
    IsRelative: bool
    Instances: tuple[str, ...]
    LeafScope: ValueObject[KEntityValue]
    RootScope: ValueObject[KEntityValue]


def RefRecords(Value: OccurRef) -> tuple[EntityRecord, ...]:
    DataId, RecipeId, XAssetId = Value.Identities
    return (
        MakeRecord(
            DataId,
            MakeGroup(
                KDataRef,
                ("OccurrenceACTRef", OccurActRef()),
                ("bEnableACTTracking", False),
                ("cachedOccurrence", LocalRef(Value.Cached)),
                ("cachedTransform", MakeMatrix(Value.Matrix)),
                ("contextFeature", None),
                ("parentFeature", LocalRef(Value.Parent)),
                ("recipe", LocalRef(XAssetId)),
                ("referenceType", Value.ReferenceKind),
                ("updateFlag", 0),
            ),
        ),
        MakeRecord(
            RecipeId,
            MakeGroup(
                KOccurRecipe,
                ("instanceIdentifiers", ValueSeries(Value.Instances)),
                ("passiveLeafComponent", Value.LeafScope),
                ("scope", Value.RootScope),
                ("srcRestructurePaths", ValueSeries(())),
            ),
            MakeGroup(KRecipe),
        ),
        MakeRecord(
            XAssetId,
            MakeGroup(
                KAssetRecipe,
                ("isRelativePath", Value.IsRelative),
                ("m_assetOccRecipe", LocalSeries((RecipeId,))),
            ),
            MakeGroup(KRecipe),
        ),
    )
