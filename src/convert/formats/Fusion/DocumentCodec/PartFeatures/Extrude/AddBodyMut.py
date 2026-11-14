from uuid import uuid4 as MakeUuid

from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.BodyRole import BodyRole


def CountLabels(Count: int, First: int = 3) -> tuple[bytes, ...]:
    return tuple(str(Index + First).encode("ascii") for Index in range(Count))


def BodyTagInfo(
    Author: AuthorState, Count: int, Operation: int, First: int = 3
) -> list[dict[str, object]]:
    return TagInfoOf(Author, CountLabels(Count, First), Operation, False)


def TagInfoOf(
    Author: AuthorState, Labels: tuple[bytes, ...], Operation: int, Primary: bool
) -> list[dict[str, object]]:
    Offsets = [0]
    for Label in Labels:
        Offsets.append(Offsets[-1] + len(Label))
    return [
        Author.MakeGroup(
            "FeatureTagInfoValue",
            dict(
                facePrimIdData=list(b"".join(Labels)),
                facePrimIdOffsets=Offsets,
                operationId=Operation,
                primary=Primary,
            ),
        )
    ]


def AddBodyRecs(Author: AuthorState, Ordinal: int, Owner: str) -> str:
    Reference = Author.Reference
    BodyUuid = Author.BodyId if Ordinal == 1 else str(MakeUuid())
    BodyName, DcBodyName = BodyRole(Ordinal, "body"), BodyRole(Ordinal, "dc_body")
    Author.Allocate(BodyName, "Body", ParentRole="bodies")
    Author.Allocate(DcBodyName, "DcBody", ParentRole="fragment")
    if Ordinal == 1:
        Author.Allocate("bodies_root", "BodiesRoot", RootName="BodiesRoot")
        Author.Allocate("body_passive_ids", "PassiveIdGenerator")
        Author.Change("body_passive_ids", rBodies=Reference("bodies"))
        Author.Change("bodies", passiveIdGenerator=Reference("body_passive_ids"))
    Author.Change(
        BodyName,
        actIdentifier=str(Author.Policy.DesignSegmentId)
        + "_"
        + str(Author.Roles[BodyName]),
        creationIndex=Ordinal,
        massProperties=Author.MakeValue("MassPropertiesValue"),
        persistentId=BodyUuid,
        rGroupParent=Reference("bodies"),
        userName=Author.SpecValue.BodyName if Ordinal == 1 else "",
    )
    Author.Change(
        DcBodyName,
        bodyUuid=BodyUuid,
        rBody=Reference(BodyName),
        rOwnFeature=Reference(Owner),
    )
    return BodyUuid


def AddBodyMut(
    Author: AuthorState,
    Prefix: str,
    Count: int,
    Operations: tuple[int, ...],
    First: int = 3,
    Labels: tuple[bytes, ...] = (),
) -> dict[str, object]:
    Ordinal = Author.FocusOrdinal
    SeedName = BodyRole(Ordinal, "body_progenitor")
    Author.Allocate(SeedName, "BodyProgenitor")
    BodyUuid = AddBodyRecs(Author, Ordinal, Prefix + "feature")
    Named = Labels or CountLabels(Count, First)
    Author.Change(
        SeedName,
        bodyUuid=BodyUuid,
        featureTagOccMap=[
            {"key": TagInfoOf(Author, Named, Operation, False), "value": 1}
            for Operation in Operations
        ],
    )
    DcBodyName = BodyRole(Ordinal, "dc_body")
    Author.Change(Prefix + "feature", dcBodies=[Author.Reference(DcBodyName)])
    return {"first": Author.Reference(SeedName), "second": Count + First}
