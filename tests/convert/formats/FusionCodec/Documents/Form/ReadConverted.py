from dataclasses import dataclass as MakeDataClass, replace as ReplaceValue
from typing import cast as CastValue

from convert.formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TagAttrib import TagAttrib
from convert.formats.Fusion.BrepCodec.Journal.Attributes.TimeAttrib import TimeAttrib
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.ExactSubtypes import (
    PcurveSpline,
    SplineCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.NegateCurve import (
    NegateCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import (
    KGrammarValue,
    KSubtypeEntry,
    SubtypeNode,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.CurveRecords import (
    ExactIntCur,
    ExpParCur,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.EntitySubtree import (
    EntitySubtree,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Subtypes.WalkSubtypes import (
    WalkSubtypes,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.CoedgeNode import CoedgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EdgeNode import EdgeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.LumpNode import LumpNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.ShellNode import ShellNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.VertexNode import VertexNode
from convert.formats.Fusion.BrepCodec.Journal.JournalEntity import KJournalEntity
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormBody,
    FormEdge,
    FormFace,
    FormSurface,
    FormUse,
    FormWindow,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormCurve import (
    FormCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.IntcurveNode import IntcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.PatchCell import PatchCell
from convert.formats.Fusion.BrepCodec.Journal.Spline.PcurveNode import PcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtransNode import SubtransNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtypeRef import SubtypeRef
from convert.formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.Reading.Materials.GroupFields import (
    GroupFields,
)
from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef

KFeatureGuid = "6C90740C-229E-4EE5-8F35-A4E5AE4F7C73"
KBodyGuid = "D3937028-C20C-4E65-B010-94AD418A5C20"
KCacheGuid = "C46D3EEB-40E1-43FA-83DC-9CB204335417"
KSerializerGuid = "40DCC3F41D-E94F-B3B1-3E95-9B6ABE572C"
KWindowNames = ("uLow", "uHigh", "vLow", "vHigh")
KTagWindows = dict[str, tuple[int, tuple[FormWindow, ...]]]
KRegionTable = tuple[tuple[PatchCell, ...], ...]


@MakeDataClass(slots=True)
class ReadState:
    Entities: tuple[KJournalEntity, ...]
    Windows: KTagWindows
    Table: tuple[KSubtypeEntry, ...]
    Edges: list[FormEdge]
    EdgeSlots: dict[int, int]
    VertexSlots: dict[int, int]
    Points: list[KJournalVector]
    Regions: list[KRegionTable]


def ActiveNodes(Model: DocumentModel) -> tuple[KJournalEntity, ...]:
    History = Model.Bodies[0].History
    assert isinstance(History, JournalModel)
    return History.Entities[: History.ActiveCount]


def HistoryMicros(Model: DocumentModel) -> int:
    Found = [
        Entity.UnixMicros
        for Entity in ActiveNodes(Model)
        if isinstance(Entity, TimeAttrib)
    ]
    assert Found and all(Number == Found[0] for Number in Found)
    return int(Found[0])


def ClearTags(Entities: tuple[KJournalEntity, ...]) -> tuple[KJournalEntity, ...]:
    Cleared: list[KJournalEntity] = []
    for Entity in Entities:
        Prefix = getattr(Entity, "Prefix", None)
        if isinstance(Prefix, EntityPrefix) and Prefix.EntityTag != -1:
            Prefix = ReplaceValue(Prefix, EntityTag=-1)
            Entity = ReplaceValue(CastValue(BodyNode, Entity), Prefix=Prefix)
        Cleared.append(Entity)
    return tuple(Cleared)


def SubtypeTable(Entities: tuple[KJournalEntity, ...]) -> tuple[KSubtypeEntry, ...]:
    return tuple(
        Found
        for Entity in Entities
        for Found in WalkSubtypes(EntitySubtree(Entity))
        if not isinstance(Found, SubtypeRef)
    )


def ResolveEntry(Value: KGrammarValue, Table: tuple[KSubtypeEntry, ...]) -> object:
    while isinstance(Value, SubtypeRef):
        Value = Table[Value.Index]
    return Value


def EntityLabel(Entities: tuple[KJournalEntity, ...], Attribute: int) -> str:
    Labels: list[str] = []
    while Attribute >= 0:
        Entry = Entities[Attribute]
        if isinstance(Entry, TagAttrib):
            Labels += [TagValue.PrimaryId for TagValue in Entry.Groups]
        Links = getattr(Entry, "Links", None)
        assert isinstance(Links, AttribLinks)
        Attribute = Links.NextAttrib
    assert len(Labels) <= 1
    return Labels[0] if Labels else ""


def ObjectWindow(ItemValue: KEntityValue) -> FormWindow:
    assert isinstance(ItemValue, ValueObject)
    Fields = GroupFields(ItemValue.Groups)
    FaceIndex = Fields["faceIndex"]
    assert type(FaceIndex) is int
    Numbers: list[float] = []
    for FieldName in KWindowNames:
        Number = Fields[FieldName]
        assert isinstance(Number, float)
        Numbers.append(Number)
    return FormWindow(FaceIndex, *Numbers)


def ClassFields(Model: DocumentModel, ClassGuid: str) -> list[dict[str, KEntityValue]]:
    return [
        GroupFields(Record.Groups)
        for Record in Model.Segments[0].Records
        if Record.IsPrimary
        and Record.Groups
        and Record.Groups[0].ClassGuid.upper() == ClassGuid
    ]


def LocalFields(Model: DocumentModel, Target: KEntityValue) -> dict[str, KEntityValue]:
    assert isinstance(Target, LocalRef)
    Found = [
        GroupFields(Record.Groups)
        for Record in Model.Segments[0].Records
        if Record.IsPrimary and Record.ObjectId == Target.ObjectId
    ]
    assert len(Found) == 1
    return Found[0]


def CachedEntity(Model: DocumentModel) -> tuple[int, int, tuple[KEntityValue, ...]]:
    (Cache,) = ClassFields(Model, KCacheGuid)
    Entity = Cache["cachedEntityId"]
    assert type(Entity) is int
    for Serializer in ClassFields(Model, KSerializerGuid):
        Generator = LocalFields(Model, Serializer["topEntityPIDGenerator"])
        NextId, Order = Generator["nextId"], Generator["scanOrderIndex"]
        assert type(NextId) is int and isinstance(Order, ValueSeries)
        if Entity in Order.Items:
            return Entity, NextId, Order.Items
    raise AssertionError("cached Form tool entity has no top-entity identity")


def BodyType(Model: DocumentModel) -> int:
    (Fields,) = ClassFields(Model, KBodyGuid)
    Value = Fields["bodyType"]
    assert type(Value) is int
    return Value


def RecordWindows(Record: EntityRecord) -> tuple[int, tuple[FormWindow, ...]]:
    Fields = GroupFields(Record.Groups)
    Items = Fields["tsEntityProgenitors"]
    EntityType = Fields["entityType"]
    assert isinstance(Items, ValueSeries) and type(EntityType) is int
    return EntityType, tuple(ObjectWindow(ItemValue) for ItemValue in Items.Items)


def TagWindows(Model: DocumentModel) -> KTagWindows:
    Owners = {
        Record.ObjectId: Record
        for Record in Model.Segments[0].Records
        if Record.IsPrimary and Record.Groups
    }
    Features = [
        Record
        for Record in Owners.values()
        if Record.Groups[0].ClassGuid.upper() == KFeatureGuid
    ]
    assert len(Features) == 1
    InfoMap = GroupFields(Features[0].Groups)["subDInfoMap"]
    assert isinstance(InfoMap, ValueMap) and len(InfoMap.Entries) == 1
    Pairing = InfoMap.Entries[0].Second
    assert isinstance(Pairing, ValuePair) and isinstance(Pairing.Second, LocalRef)
    TagVector = GroupFields(Owners[Pairing.Second.ObjectId].Groups)["ProgenitorTagVec"]
    assert isinstance(TagVector, ValueSeries)
    Found: KTagWindows = {}
    for Entry in TagVector.Items:
        assert isinstance(Entry, ValuePair) and isinstance(Entry.First, LocalRef)
        Found[str(Entry.Second)] = RecordWindows(Owners[Entry.First.ObjectId])
    return Found


def FaceChain(Entities: tuple[KJournalEntity, ...]) -> list[int]:
    Bodies = [Entity for Entity in Entities if isinstance(Entity, BodyNode)]
    assert len(Bodies) == 1
    LumpValue = Entities[Bodies[0].FirstLump]
    assert isinstance(LumpValue, LumpNode)
    ShellValue = Entities[LumpValue.FirstShell]
    assert isinstance(ShellValue, ShellNode)
    Chain: list[int] = []
    Current = ShellValue.FirstFace
    while Current >= 0:
        Chain.append(Current)
        FaceValue = Entities[Current]
        assert isinstance(FaceValue, FaceNode)
        Current = FaceValue.NextFace
    return Chain


def LoopUses(Entities: tuple[KJournalEntity, ...], FaceIndex: int) -> list[int]:
    FaceValue = Entities[FaceIndex]
    assert isinstance(FaceValue, FaceNode)
    LoopValue = Entities[FaceValue.FirstLoop]
    assert isinstance(LoopValue, LoopNode) and LoopValue.NextLoop == -1
    Chain = [LoopValue.FirstCoedge]
    while True:
        Coedge = Entities[Chain[-1]]
        assert isinstance(Coedge, CoedgeNode)
        if Coedge.NextCoedge == LoopValue.FirstCoedge:
            return Chain
        Chain.append(Coedge.NextCoedge)


def FloatList(Value: KGrammarValue) -> tuple[float, ...]:
    assert type(Value) is tuple
    Numbers: list[float] = []
    for Number in Value:
        assert isinstance(Number, float)
        Numbers.append(Number)
    return tuple(Numbers)


def CurveJumps(Value: SubtypeNode) -> tuple[tuple[float, ...], ...]:
    Record = Value.Body
    assert isinstance(Record, ExactIntCur)
    return tuple(FloatList(Entry) for Entry in Record.Context.Discontinuities)


def VertexSlotMut(State: ReadState, Index: int) -> int:
    if Index not in State.VertexSlots:
        Vertex = State.Entities[Index]
        assert isinstance(Vertex, VertexNode)
        Point = State.Entities[Vertex.PointRef]
        assert isinstance(Point, PointNode)
        State.VertexSlots[Index] = len(State.Points)
        State.Points.append(Point.PositionCm)
    return State.VertexSlots[Index]


def EdgeSlotMut(State: ReadState, Index: int) -> int:
    if Index in State.EdgeSlots:
        return State.EdgeSlots[Index]
    EdgeValue = State.Entities[Index]
    assert isinstance(EdgeValue, EdgeNode) and not EdgeValue.Reversed
    Carrier = State.Entities[EdgeValue.CurveRef]
    assert isinstance(Carrier, IntcurveNode) and not Carrier.Reversed
    assert isinstance(Carrier.Curve, SubtypeNode)
    Curve = SplineCurve(Carrier.Curve)
    Jumps = CurveJumps(Carrier.Curve)
    assert FormCurve(Curve, Jumps) == Carrier.Curve
    Bounds = (EdgeValue.StartParam, EdgeValue.EndParam)
    Label = EntityLabel(State.Entities, EdgeValue.Prefix.Attribute)
    Start = VertexSlotMut(State, EdgeValue.StartVertex)
    Final = VertexSlotMut(State, EdgeValue.EndVertex)
    Windows = State.Windows[Label][1] if Label else ()
    Shape = FormEdge(Start, Final, Curve, Jumps, EdgeValue.Convexity, Label, Windows)
    if Bounds != (Curve.Knots[0], Curve.Knots[-1]):
        Shape = ReplaceValue(Shape, Bounds=Bounds)
    State.EdgeSlots[Index] = len(State.Edges)
    State.Edges.append(Shape)
    return State.EdgeSlots[Index]


def CheckShift(Surface: TsplineSurf, OffsetU: float, OffsetV: float) -> None:
    Cache = Surface.Cache
    for Offset, Knots, Closure in (
        (OffsetU, Cache.KnotsU, Cache.ClosureU),
        (OffsetV, Cache.KnotsV, Cache.ClosureV),
    ):
        Period = Knots[-1].Value - Knots[0].Value
        assert Offset == 0.0 or (Closure != 0 and abs(Offset) == Period)


def ReadUseMut(State: ReadState, Index: int, Region: int) -> FormUse:
    Coedge = State.Entities[Index]
    assert isinstance(Coedge, CoedgeNode)
    Carrier = State.Entities[Coedge.Pcurve]
    assert isinstance(Carrier, PcurveNode) and not Carrier.Reversed
    assert isinstance(Carrier.Curve, SubtypeNode)
    Trace = PcurveSpline(Carrier.Curve)
    Members = Carrier.Curve.Body
    assert isinstance(Members, ExpParCur)
    Holder = Members.Surface
    assert type(Holder.Body) is tuple
    Surface = ResolveEntry(Holder.Body[1], State.Table)
    assert isinstance(Surface, TsplineSurf) and Surface.FaceIndex == Region
    CheckShift(Surface, Carrier.OffsetU, Carrier.OffsetV)
    Trace = NegateCurve(Trace) if Coedge.Reversed else Trace
    EdgeIndex = EdgeSlotMut(State, Coedge.EdgeRef)
    return FormUse(EdgeIndex, Coedge.Reversed, Trace, Members.FitTolerance)


def ReadFaceMut(State: ReadState, Index: int) -> FormFace:
    FaceValue = State.Entities[Index]
    assert isinstance(FaceValue, FaceNode)
    Carrier = State.Entities[FaceValue.Surface]
    assert isinstance(Carrier, SplineNode)
    Surface = ResolveEntry(Carrier.Surface, State.Table)
    assert isinstance(Surface, TsplineSurf)
    Scope = ResolveEntry(Surface.Subtrans, State.Table)
    assert isinstance(Scope, SubtransNode)
    State.Regions.append(Scope.Regions)
    SideUses = tuple(
        ReadUseMut(State, UseIndex, Surface.FaceIndex)
        for UseIndex in LoopUses(State.Entities, Index)
    )
    Shape = FormSurface(Surface.Cache, Surface.Jumps, Surface.FaceIndex)
    Label = EntityLabel(State.Entities, FaceValue.Prefix.Attribute)
    return FormFace(Shape, SideUses, Label, FaceValue.DoubleSided, FaceValue.Contained)


def ReadConverted(Model: DocumentModel) -> FormBody:
    assert len(Model.Forms) == 1 and len(Model.Bodies) == 1
    Entities = ActiveNodes(Model)
    State = ReadState(
        Entities, TagWindows(Model), SubtypeTable(Entities), [], {}, {}, [], []
    )
    Faces = tuple(ReadFaceMut(State, FaceIndex) for FaceIndex in FaceChain(Entities))
    assert State.Regions and len(set(State.Regions)) == 1
    return FormBody(tuple(State.Points), tuple(State.Edges), Faces, State.Regions[0])
