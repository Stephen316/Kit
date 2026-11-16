from pytest import mark as MarkTests

from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.Formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.EntityCodec.Model.OptionalValue import OptionalValue
from convert.Formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from tests.Convert.Formats.FusionCodec.Documents.PartFeatures.BulletinRefs import (
    IsIdentityRef,
)
from tests.Convert.Formats.FusionCodec.Documents.PartFeatures.PartCases import (
    KPartCases,
    PartSpec,
)
from tests.Convert.Formats.FusionCodec.Documents.PartFeatures.PartRecords import (
    PartRecords,
)


# shared chain owners setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def ChainOwners(History: JournalModel) -> dict[int, int]:
    Links: dict[int, set[int]] = {}
    for State in History.States:
        for Board in State.Boards:
            for Change in Board.Changes:
                if Change.OldRef >= 0 and Change.NewRef >= 0:
                    Links.setdefault(Change.OldRef, set()).add(Change.NewRef)
                    Links.setdefault(Change.NewRef, set()).add(Change.OldRef)
    Owners: dict[int, int] = {}
    for Start in range(len(History.Entities)):
        Pending = [Start]
        while Pending:
            Index = Pending.pop()
            if Index not in Owners:
                Owners[Index] = Start
                Pending.extend(Links.get(Index, set()))
    return Owners


# shared scope ids setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
def ScopeIds(Value: KEntityValue) -> tuple[KEntityValue, ...]:
    Inner = Value.Value if isinstance(Value, OptionalValue) else Value
    assert isinstance(Inner, ValueObject)
    return tuple(
        FieldValue.Value
        for Group in Inner.Groups
        for FieldValue in Group.Fields
        if FieldValue.FieldName == "scopeEntityIdentifier"
    )


# the tag chains contract needs boundary coverage so stored document relationships remain consistent
@MarkTests.parametrize("NameValue", tuple(KPartCases))
def TestTagChains(NameValue: str) -> None:
    Model = ReadDocument(EmitDocument(PartSpec(NameValue)))
    History = Model.Bodies[0].History
    assert isinstance(History, JournalModel)
    Owners = ChainOwners(History)
    Chains: dict[int, set[int]] = {}
    for Index, Entity in enumerate(History.Entities):
        TagValue = getattr(getattr(Entity, "Prefix", None), "EntityTag", -1)
        if isinstance(TagValue, int) and TagValue >= 0:
            Chains.setdefault(TagValue, set()).add(Owners[Index])
    assert Chains and all(len(Owned) == 1 for Owned in Chains.values())
    assert max(Chains) < History.Stream.NextEntityTag
    BodyTags = [
        Entity.Prefix.EntityTag
        for Entity in History.Entities[: History.ActiveCount]
        if isinstance(Entity, BodyNode)
    ]
    assert BodyTags == [0]


# the reference scope contract needs boundary coverage so stored document relationships remain consistent
@MarkTests.parametrize("NameValue", tuple(KPartCases))
def TestRefScope(NameValue: str) -> None:
    Model = ReadDocument(EmitDocument(PartSpec(NameValue)))
    Components = PartRecords(Model, "Component")
    assert len(Components) == 1
    Expected = (Components[0]["persistentId"],)
    Picks = PartRecords(Model, "BrepRef")
    assert len(Picks) == len(KPartCases[NameValue])
    Scopes = [ScopeIds(Fields["rScope"]) for Fields in Picks]
    Scopes.extend(
        ScopeIds(Fields["scope"]) for Fields in PartRecords(Model, "ETCachedTopology")
    )
    assert all(Found == Expected for Found in Scopes)


# the bulletin ids contract needs boundary coverage so stored document relationships remain consistent
@MarkTests.parametrize("NameValue", tuple(KPartCases))
def TestBulletinIds(NameValue: str) -> None:
    Model = ReadDocument(EmitDocument(PartSpec(NameValue)))
    History = Model.Bodies[0].History
    assert isinstance(History, JournalModel)
    assert IsIdentityRef(History)
