from convert.formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.LinkAuthor.Model.RootFacts import RootFacts
from convert.formats.Fusion.LinkAuthor.Records.LinkGuids import (
    KActRefValue,
    KBasePath,
    KOccurActRef,
    KOccurPath,
    KOccurState,
    KPassivePath,
    KPassiveScope,
)
from convert.formats.Fusion.LinkAuthor.Records.RecordValues import (
    MakeGroup,
    PlaceMatrix,
)
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


def BaseGroup(
    RootInfo: RootFacts | None, Identities: tuple[int, ...]
) -> EntityGroup[KEntityValue]:
    Passive = ValueObject(
        (MakeGroup(KPassivePath, ("instanceIds", ValueSeries(Identities))),)
    )
    return MakeGroup(
        KBasePath,
        ("componentInstances", ValueSeries(())),
        ("creationState", 3),
        ("passiveOccurrencePath", Passive),
        (
            "sourceACTComponent",
            (
                None
                if RootInfo is None
                else SegmentRef(RootInfo.ActComponent, RootInfo.ActSegment)
            ),
        ),
        ("sourceComponent", None if RootInfo is None else LocalRef(RootInfo.Component)),
    )


def OccurPath(
    RootInfo: RootFacts, Identities: tuple[int, ...]
) -> ValueObject[KEntityValue]:
    return ValueObject((MakeGroup(KOccurPath), BaseGroup(RootInfo, Identities)))


def BasePathValue(
    RootInfo: RootFacts, Identities: tuple[int, ...]
) -> ValueObject[KEntityValue]:
    return ValueObject((BaseGroup(RootInfo, Identities),))


def ScopeValue(
    AssetId: str, EntityName: str, ScopeKind: int
) -> ValueObject[KEntityValue]:
    return ValueObject(
        (
            MakeGroup(
                KPassiveScope,
                ("assetId", AssetId),
                ("scopeEntityIdentifier", EntityName),
                ("scopeIdType", ScopeKind),
                ("segmentId", 0),
            ),
        )
    )


def StateValue(
    IsGround: bool, Feature: int, Matrix: tuple[float, ...]
) -> ValueObject[KEntityValue]:
    return ValueObject(
        (
            MakeGroup(
                KOccurState,
                ("isActive", True),
                ("isGround", IsGround),
                ("rDcFeature", LocalRef(Feature)),
                ("transform", PlaceMatrix(Matrix)),
            ),
        )
    )


def EmptyActRef() -> ValueObject[KEntityValue]:
    return ValueObject(
        (
            MakeGroup(
                KActRefValue,
                ("actRefdTable", None),
                ("changeTypesToTrack", ValueSeries(())),
                ("crossAsset", False),
                ("owningEntity", None),
                ("rActData", None),
                ("refdEntity", None),
            ),
        )
    )


def OccurActRef() -> ValueObject[KEntityValue]:
    return ValueObject(
        (
            MakeGroup(
                KOccurActRef,
                ("actDataForCIs", ValueSeries(())),
                ("actRef", EmptyActRef()),
                ("deepTracking", False),
                ("path", ValueObject((BaseGroup(None, ()),))),
                ("topCompActRef", EmptyActRef()),
            ),
        )
    )
