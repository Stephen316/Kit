from convert.Formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.Formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.Formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.Formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.Formats.Fusion.LinkAuthor.Model.RootFacts import RootFacts
from convert.Formats.Fusion.LinkAuthor.Records.LinkGuids import (
    KActRefValue,
    KBasePath,
    KOccurActRef,
    KOccurPath,
    KOccurState,
    KPassivePath,
    KPassiveScope,
)
from convert.Formats.Fusion.LinkAuthor.Records.RecordValues import (
    MakeGroup,
    PlaceMatrix,
)
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# the base group contract needs a shared interpretation so cross document references retain their intended ownership
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


# the occur path contract needs a shared interpretation so cross document references retain their intended ownership
def OccurPath(
    RootInfo: RootFacts, Identities: tuple[int, ...]
) -> ValueObject[KEntityValue]:
    return ValueObject((MakeGroup(KOccurPath), BaseGroup(RootInfo, Identities)))


# the base path value contract needs a shared interpretation so cross document references retain their intended ownership
def BasePathValue(
    RootInfo: RootFacts, Identities: tuple[int, ...]
) -> ValueObject[KEntityValue]:
    return ValueObject((BaseGroup(RootInfo, Identities),))


# the scope value contract needs a shared interpretation so cross document references retain their intended ownership
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


# the state value contract needs a shared interpretation so cross document references retain their intended ownership
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


# the empty act reference contract needs a shared interpretation so cross document references retain their intended ownership
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


# the occur act reference contract needs a shared interpretation so cross document references retain their intended ownership
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
