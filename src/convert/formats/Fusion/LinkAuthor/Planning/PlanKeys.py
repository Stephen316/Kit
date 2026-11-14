from collections.abc import Iterator
from itertools import count as CountFrom
from itertools import islice as SliceItems
from uuid import uuid4 as MakeUuid

from convert.formats.Fusion.LinkAuthor.Model.ActionKeys import ActionKeys
from convert.formats.Fusion.LinkAuthor.Model.AssemblyPlan import AssemblyPlan
from convert.formats.Fusion.LinkAuthor.Model.AssemblySpec import AssemblySpec
from convert.formats.Fusion.LinkAuthor.Model.LinkKeys import LinkKeys
from convert.formats.Fusion.LinkAuthor.Model.PlaceKeys import PlaceKeys
from convert.formats.Fusion.LinkAuthor.Model.RootFacts import RootFacts
from convert.formats.Fusion.LinkAuthor.Model.TargetFacts import TargetFacts


def TakeIdsMut(Source: Iterator[int], Total: int) -> tuple[int, ...]:
    return tuple(SliceItems(Source, Total))


def MakeLinks(Total: int) -> tuple[LinkKeys, ...]:
    Tokens: list[int] = []
    while len(Tokens) < Total * 2:
        Token = MakeUuid().int >> 64
        if Token and Token not in Tokens:
            Tokens.append(Token)
    return tuple(
        LinkKeys(
            str(MakeUuid()), str(MakeUuid()), Tokens[Index * 2], Tokens[Index * 2 + 1]
        )
        for Index in range(Total)
    )


def PlanPlaceMut(
    Sources: tuple[Iterator[int], Iterator[int], Iterator[int]],
    Facts: TargetFacts,
    Numbers: tuple[int, int, int],
) -> PlaceKeys:
    Design, Tracking, Browser = Sources
    Instance, NodeId, NodeData, Feature, FeatureData, Status, Table, Occurrence = (
        TakeIdsMut(Design, 8)
    )
    Nested = TakeIdsMut(Design, len(Facts.Children))
    ActInstance, ActData, ActTable, ActCopy = TakeIdsMut(Tracking, 4)
    InstanceId, FeatureId, FeatureIndex = Numbers
    return PlaceKeys(
        Instance,
        NodeId,
        NodeData,
        Feature,
        FeatureData,
        Status,
        Table,
        Occurrence,
        Nested,
        str(MakeUuid()),
        InstanceId,
        FeatureId,
        FeatureIndex,
        ActInstance,
        ActData,
        ActTable,
        ActCopy,
        next(Browser),
    )


def PlanPinMut(Design: Iterator[int], FeatureId: int, FeatureIndex: int) -> ActionKeys:
    Override, Feature, DataId, RecipeId, XAssetId, FeatureData, Status, Table = (
        TakeIdsMut(Design, 8)
    )
    return ActionKeys(
        Feature,
        FeatureData,
        Status,
        Table,
        FeatureId,
        FeatureIndex,
        (Override, DataId, RecipeId, XAssetId),
    )


def PlanJointMut(Design: Iterator[int], FeatureId: int) -> ActionKeys:
    JointId, Feature = TakeIdsMut(Design, 2)
    References = TakeIdsMut(Design, 9)
    FeatureData, Status, Table, DcOccurId, JointOccId = TakeIdsMut(Design, 5)
    return ActionKeys(
        Feature,
        FeatureData,
        Status,
        Table,
        FeatureId,
        1,
        (JointId, *References, DcOccurId, JointOccId),
    )


def PlanKeys(
    RootInfo: RootFacts,
    Request: AssemblySpec,
    Facts: tuple[TargetFacts, ...],
    Starts: tuple[int, int, int],
) -> AssemblyPlan:
    Sources = (CountFrom(Starts[0]), CountFrom(Starts[1]), CountFrom(Starts[2]))
    Features = CountFrom(RootInfo.SeedId)
    XRefId = next(Sources[0])
    Places: list[PlaceKeys] = []
    Pinnings: list[ActionKeys | None] = []
    for Index, Placement in enumerate(Request.Placements):
        Numbers = (RootInfo.InstanceSeed + Index, next(Features), Index + 1)
        Places.append(PlanPlaceMut(Sources, Facts[Placement.TargetIndex], Numbers))
        PinIndex = sum(1 for Entry in Pinnings if Entry is not None) + 1
        Pinnings.append(
            PlanPinMut(Sources[0], next(Features), PinIndex)
            if Placement.Grounded
            else None
        )
    Joint = None if Request.Joint is None else PlanJointMut(Sources[0], next(Features))
    return AssemblyPlan(
        XRefId,
        tuple(Places),
        tuple(Pinnings),
        Joint,
        MakeLinks(len(Request.Targets)),
        next(Sources[0]),
        next(Sources[1]),
        next(Sources[2]),
        next(Features),
        RootInfo.InstanceSeed + len(Places),
    )
