from convert.formats.Fusion.EntityCodec.Model.EntityFrame import EntityFrame
from convert.formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
from convert.formats.Fusion.EntityCodec.Model.NamedValue import NamedValue
from convert.formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.LinkAuthor.Records.LinkGuids import KManagedEntity
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef

KPlainFrame = EntityFrame("", None, None)

KIdentity = (
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
)


def MakeGroup(
    ClassGuid: str, *Fields: tuple[str, KEntityValue]
) -> EntityGroup[KEntityValue]:
    return EntityGroup(
        ClassGuid, tuple(NamedValue(FieldName, Value) for FieldName, Value in Fields)
    )


def MakeRecord(ObjectId: int, *Groups: EntityGroup[KEntityValue]) -> EntityRecord:
    return EntityRecord(ObjectId, 0, True, KPlainFrame, Groups)


def FrameRecord(
    ObjectId: int, Frame: EntityFrame, *Groups: EntityGroup[KEntityValue]
) -> EntityRecord:
    return EntityRecord(ObjectId, 0, True, Frame, Groups)


def ParentRecord(ObjectId: int, Parent: int | None) -> EntityRecord:
    Target = None if Parent is None else LocalRef(Parent)
    return EntityRecord(
        ObjectId,
        0,
        False,
        KPlainFrame,
        (MakeGroup(KManagedEntity, ("rParent", Target)),),
    )


def LocalSeries(Identities: tuple[int, ...]) -> ValueSeries[KEntityValue]:
    return ValueSeries(tuple(LocalRef(Identity) for Identity in Identities))


def TextPairs(Pairs: tuple[tuple[str, str], ...]) -> ValueMap[KEntityValue]:
    return ValueMap(tuple(ValuePair(First, Second) for First, Second in Pairs))


def MakeMatrix(Entries: tuple[float, ...] | None) -> MatrixValue:
    return MatrixValue(None if Entries is None else tuple(Entries))


def PlaceMatrix(Entries: tuple[float, ...]) -> MatrixValue:
    return MatrixValue(None if Entries == KIdentity else tuple(Entries))
