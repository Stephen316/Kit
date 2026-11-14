from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.CurveRecords import (
    ExpParCur,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    ChoiceValue,
    KSubtypeValue,
    SubtypeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.EntitySubtree import (
    EntitySubtree,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.WalkSubtypes import (
    WalkSubtypes,
)
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.Permutation.RemapEntity import RemapEntity
from convert.formats.Fusion.BrepCodec.Journal.Spline.CheckSubtypes import (
    CheckSubtypes,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.MakeFormNodes import (
    FormDraft,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.PcurveNode import PcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtransNode import SubtransNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef
from convert.formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf
from convert.formats.Fusion.BrepCodec.Journal.Writing.MakeEntityNode import (
    MakeEntityNode,
)


def BreadthOrder(Entities: tuple[KJournalEntity, ...]) -> tuple[int, ...]:
    Order = [0, 1]
    Visited = {0, 1}
    Cursor = 1
    while Cursor < len(Order):
        Tokens = MakeEntityNode(Entities[Order[Cursor]]).Tokens
        Cursor += 1
        for TagValue, Field in Tokens:
            if TagValue == 12 and isinstance(Field, int) and Field not in Visited:
                if Field >= 0:
                    Visited.add(Field)
                    Order.append(Field)
    if len(Order) != len(Entities):
        raise ValueError("Converted Form BRep has records unreachable from its body")
    return tuple(Order)


def PlaceSurface(Entity: KJournalEntity, Surface: KSubtypeValue) -> KJournalEntity:
    if isinstance(Entity, SplineNode):
        return ReplaceValue(Entity, Surface=Surface)
    if not isinstance(Entity, PcurveNode) or not isinstance(Entity.Curve, SubtypeNode):
        raise ValueError("Converted Form surface carrier has an unexpected record")
    CurveBody = Entity.Curve.Body
    if not isinstance(CurveBody, ExpParCur):
        raise ValueError("Converted Form pcurve has an unexpected body")
    Carrier = ChoiceValue("spline", (False, Surface, (None, None, None, None)))
    Changed = ReplaceValue(CurveBody, Surface=Carrier)
    return ReplaceValue(Entity, Curve=SubtypeNode("exp_par_cur", Changed))


def SettleSurfaces(
    Entities: tuple[KJournalEntity, ...],
    Carriers: tuple[int, ...],
    Surfaces: tuple[TsplineSurf, ...],
) -> tuple[KJournalEntity, ...]:
    Defined: dict[int, int] = {}
    Scope: int | None = None
    Counter = 0
    Results: list[KJournalEntity] = []
    for Entity, Carrier in zip(Entities, Carriers, strict=True):
        if Carrier >= 0:
            Known = Defined.get(Carrier)
            Inline = Surfaces[Carrier]
            if Scope is not None:
                Inline = ReplaceValue(Inline, Subtrans=SubtypeRef("subtrans", Scope))
            Value = Inline if Known is None else SubtypeRef("surface", Known)
            Entity = PlaceSurface(Entity, Value)
        Found = tuple(
            Entry
            for Entry in WalkSubtypes(EntitySubtree(Entity))
            if not isinstance(Entry, SubtypeRef)
        )
        for Offset, Entry in enumerate(Found):
            if isinstance(Entry, TsplineSurf):
                Defined[Carrier] = Counter + Offset
            if isinstance(Entry, SubtransNode):
                Scope = Counter + Offset
        Counter += len(Found)
        Results.append(Entity)
    return tuple(Results)


def OrderFormNodes(Draft: FormDraft) -> tuple[KJournalEntity, ...]:
    Order = BreadthOrder(Draft.Entities)
    Positions = [0] * len(Order)
    for Position, Index in enumerate(Order):
        Positions[Index] = Position
    Mapping = tuple(Positions)
    Moved = tuple(RemapEntity(Draft.Entities[Index], Mapping) for Index in Order)
    Carriers = tuple(Draft.Carriers[Index] for Index in Order)
    Result = SettleSurfaces(Moved, Carriers, Draft.Surfaces)
    CheckSubtypes(Result)
    return Result
