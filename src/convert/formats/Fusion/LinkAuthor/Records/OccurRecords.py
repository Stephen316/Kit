from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.LinkAuthor.MatrixMath import ComposeMatrix
from convert.formats.Fusion.LinkAuthor.Model.PlaceKeys import PlaceKeys
from convert.formats.Fusion.LinkAuthor.Model.RootFacts import RootFacts
from convert.formats.Fusion.LinkAuthor.Model.TargetFacts import TargetFacts
from convert.formats.Fusion.LinkAuthor.Records.LinkGuids import KDcOccurrence
from convert.formats.Fusion.LinkAuthor.Records.PathValues import (
    OccurPath,
    StateValue,
)
from convert.formats.Fusion.LinkAuthor.Records.RecordValues import (
    MakeGroup,
    MakeRecord,
)


def OccurRecord(
    RootInfo: RootFacts,
    ObjectId: int,
    Identities: tuple[int, ...],
    States: tuple[ValueObject[KEntityValue], ...],
) -> EntityRecord:
    return MakeRecord(
        ObjectId,
        MakeGroup(
            KDcOccurrence,
            ("contextPositionMap", ValueMap(())),
            ("dcAssyConstraintOccurrences", ValueSeries(())),
            ("path", OccurPath(RootInfo, Identities)),
            ("stateIdx", len(States) - 1),
            ("states", ValueSeries(States)),
        ),
    )


def OccurRecords(
    RootInfo: RootFacts,
    Facts: TargetFacts,
    KeySet: PlaceKeys,
    Matrix: tuple[float, ...],
    PinFeature: int | None,
) -> tuple[EntityRecord, ...]:
    States: tuple[ValueObject[KEntityValue], ...] = (
        StateValue(False, KeySet.Feature, Matrix),
    )
    if PinFeature is not None:
        States = (*States, StateValue(True, PinFeature, Matrix))
    if len(KeySet.Nested) != len(Facts.Children):
        raise ValueError("Fusion nested occurrence plan disagrees with its target")
    Nested = tuple(
        OccurRecord(
            RootInfo,
            ObjectId,
            (KeySet.InstanceId, ChildId),
            (StateValue(False, KeySet.Feature, ComposeMatrix(Matrix, ChildMatrix)),),
        )
        for ObjectId, (ChildId, ChildMatrix) in zip(KeySet.Nested, Facts.Children)
    )
    return (
        OccurRecord(RootInfo, KeySet.Occurrence, (KeySet.InstanceId,), States),
        *Nested,
    )
