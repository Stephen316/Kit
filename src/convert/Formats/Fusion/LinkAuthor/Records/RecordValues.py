from convert.Formats.Fusion.EntityCodec.Model.EntityFrame import EntityFrame
from convert.Formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.Formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.Formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
from convert.Formats.Fusion.EntityCodec.Model.NamedValue import NamedValue
from convert.Formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.Formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.Formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.Formats.Fusion.LinkAuthor.Records.LinkGuids import KManagedEntity
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef

# plain frame must remain consistent across callers so cross document references retain their intended ownership
KPlainFrame = EntityFrame("", None, None)

# the identity order must stay explicit so cross document references retain their intended ownership
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


# the group operation needs a consistent construction rule so cross document references retain their intended ownership
def MakeGroup(
    ClassGuid: str, *Fields: tuple[str, KEntityValue]
) -> EntityGroup[KEntityValue]:
    return EntityGroup(
        ClassGuid, tuple(NamedValue(FieldName, Value) for FieldName, Value in Fields)
    )


# the record operation needs a consistent construction rule so cross document references retain their intended ownership
def MakeRecord(ObjectId: int, *Groups: EntityGroup[KEntityValue]) -> EntityRecord:
    return EntityRecord(ObjectId, 0, True, KPlainFrame, Groups)


# the frame record contract needs a shared interpretation so cross document references retain their intended ownership
def FrameRecord(
    ObjectId: int, Frame: EntityFrame, *Groups: EntityGroup[KEntityValue]
) -> EntityRecord:
    return EntityRecord(ObjectId, 0, True, Frame, Groups)


# the parent record contract needs a shared interpretation so cross document references retain their intended ownership
def ParentRecord(ObjectId: int, Parent: int | None) -> EntityRecord:
    Target = None if Parent is None else LocalRef(Parent)
    return EntityRecord(
        ObjectId,
        0,
        False,
        KPlainFrame,
        (MakeGroup(KManagedEntity, ("rParent", Target)),),
    )


# the local series contract needs a shared interpretation so cross document references retain their intended ownership
def LocalSeries(Identities: tuple[int, ...]) -> ValueSeries[KEntityValue]:
    return ValueSeries(tuple(LocalRef(Identity) for Identity in Identities))


# the text pairs contract needs a shared interpretation so cross document references retain their intended ownership
def TextPairs(Pairs: tuple[tuple[str, str], ...]) -> ValueMap[KEntityValue]:
    return ValueMap(tuple(ValuePair(First, Second) for First, Second in Pairs))


# the matrix operation needs a consistent construction rule so cross document references retain their intended ownership
def MakeMatrix(Entries: tuple[float, ...] | None) -> MatrixValue:
    return MatrixValue(None if Entries is None else tuple(Entries))


# the matrix operation needs a consistent construction rule so cross document references retain their intended ownership
def PlaceMatrix(Entries: tuple[float, ...]) -> MatrixValue:
    return MatrixValue(None if Entries == KIdentity else tuple(Entries))
