from math import sqrt as SquareRoot
from uuid import UUID

from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftLinks import (
    KNullHard,
    KNullSoft,
    HandleNumber,
    HardOwner,
    HardPointer,
    SoftPointer,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftRow import DraftEed
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import (
    DraftRecord,
    KDraftValue,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.PlaceMut import PlaceMut
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetKeys import (
    KFusionSource,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.ViewSource import ViewSource
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Views.ViewKeys import ViewKeys
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Views.ViewPlan import ViewPlan

# the point triple shape must stay shared so drawing view authoring uses one contract for compatible values
KPointTriple = tuple[float, float, float]

# body bits must remain consistent across callers so projected geometry retains its paper and model relationships
KBodyBits = 0x8000000001

# matrix head must remain consistent across callers so projected geometry retains its paper and model relationships
KMatrixHead = 0x40

# the matrix names order must stay explicit so projected geometry retains its paper and model relationships
KMatrixNames = ("XX", "XY", "XZ", "X", "YX", "YY", "YZ", "Y", "ZX", "ZY", "ZZ", "Z")

# the base shape order must stay explicit so projected geometry retains its paper and model relationships
KBaseShape = (11, 3104)

# the child shape order must stay explicit so projected geometry retains its paper and model relationships
KChildShape = (15, 40032)

# visible style must remain consistent across callers so projected geometry retains its paper and model relationships
KVisibleStyle = 2

# hidden style must remain consistent across callers so projected geometry retains its paper and model relationships
KHiddenStyle = 1

# inherit style must remain consistent across callers so projected geometry retains its paper and model relationships
KInheritStyle = 4


# the body key contract needs a shared interpretation so projected geometry retains its paper and model relationships
def BodyKey() -> tuple[tuple[str, KDraftValue], ...]:
    return (("KeyLong", 0), ("KeyBits", KBodyBits), ("KeyFlag", 0))


# the matrix items contract needs a shared interpretation so projected geometry retains its paper and model relationships
def MatrixItems() -> tuple[tuple[str, KDraftValue], ...]:
    Values = (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
    return tuple(
        (("Offset" if len(Called) == 1 else "Matrix") + Called, Value)
        for Called, Value in zip(KMatrixNames, Values)
    )


# guid items needs an explicit validity boundary so projected geometry retains its paper and model relationships
def GuidItems(GuidText: str) -> tuple[tuple[str, KDraftValue], ...]:
    try:
        Parsed = UUID(GuidText)
    except ValueError as Failure:
        raise ValueError(
            f"Authored DWG body GUID {GuidText!r} is malformed"
        ) from Failure
    HeadPart, MiddlePart, LowPart = Parsed.fields[0:3]
    return (
        ("GuidHead", HeadPart),
        ("GuidMiddle", MiddlePart),
        ("GuidLow", LowPart),
        ("GuidTail", Parsed.bytes[8:]),
        ("GuidFlag", 0),
    )


# body path needs an explicit validity boundary so projected geometry retains its paper and model relationships
def BodyPath(Source: ViewSource) -> tuple[DraftRecord, ...]:
    Chain = (*Source.OccurrencePath, Source.BodyId, Source.BodyId)
    if any(LinkId <= 0 for LinkId in Chain):
        raise ValueError("Authored DWG body path needs positive entity ids")
    return tuple(DraftRecord((("PathId", LinkId),)) for LinkId in Chain)


# the view body contract needs a shared interpretation so projected geometry retains its paper and model relationships
def ViewBody(Source: ViewSource, Edges: tuple[DraftRecord, ...]) -> DraftRecord:
    Leading = (*GuidItems(Source.GeometryGuid), ("MatrixHead", KMatrixHead))
    BodyChain = BodyPath(Source)
    Longs = tuple((Called, 0) for Called in ("BodyLongA", "BodyLongB", "BodyLongC"))
    Closing = (
        ("BodyFlagA", 0),
        ("BodyFlagB", 1),
        ("PathCount", len(BodyChain)),
        ("Path", BodyChain),
        ("BodyLongD", 1),
        ("BodyLongE", 4294967295),
        ("EdgeCount", len(Edges)),
        ("Edges", Edges),
    )
    return DraftRecord((*BodyKey(), *Leading, *MatrixItems(), *Longs, *Closing))


# the body key row contract needs a shared interpretation so projected geometry retains its paper and model relationships
def BodyKeyRow(Source: ViewSource) -> DraftRecord:
    BodyChain = BodyPath(Source)
    return DraftRecord(
        (
            *BodyKey(),
            ("KeyLongB", 0),
            ("PathCount", len(BodyChain)),
            ("Path", BodyChain),
            ("KeyFlagB", 0),
        )
    )


# the trail fields contract needs a shared interpretation so projected geometry retains its paper and model relationships
def TrailFields(
    KeySet: ViewKeys, Planned: ViewPlan, Source: ViewSource
) -> dict[str, KDraftValue]:
    return {
        "ViewCenter": Planned.Center,
        "TrailLongA": 0,
        "TrailFlagA": 1,
        "TrailLongB": 0,
        "TrailLongC": 0,
        "TrailLongD": 0,
        "TrailFlagB": 1,
        "HolderCount": 0,
        "HolderKeys": (),
        "BodyKeyCount": 1,
        "BodyKeys": (BodyKeyRow(Source),),
        "TextA": "",
        "TextB": "",
        "BlockRef": SoftPointer(KeySet.InnerRef),
        "DrawingView": SoftPointer(KeySet.Drawing),
        "FusionSource": HardPointer(KFusionSource),
        "Orientation": HardOwner(KeySet.ViewRep + "/Orientation"),
        "OrientationDef": HardOwner(KeySet.ViewRep + "/Definition"),
        "NullA": KNullSoft,
        "Viewport": SoftPointer(KeySet.Frame),
        "NullB": KNullHard,
        "SelfRef": SoftPointer(KeySet.ViewRep),
        "ModelBlockRef": SoftPointer(KeySet.ModelRef),
        "NullC": KNullSoft,
        "ProjectedHolders": (),
        "NullD": KNullHard,
    }


# the view style contract needs a shared interpretation so projected geometry retains its paper and model relationships
def ViewStyle(Planned: ViewPlan, IsBase: bool) -> int:
    Style = KHiddenStyle if Planned.ShowHidden else KVisibleStyle
    return Style if IsBase else KInheritStyle + Style


# the view fields contract needs a shared interpretation so projected geometry retains its paper and model relationships
def ViewFields(
    KeySet: ViewKeys,
    Planned: ViewPlan,
    IsBase: bool,
    Source: ViewSource,
    Edges: tuple[DraftRecord, ...],
) -> dict[str, KDraftValue]:
    LongA, Flags = KBaseShape if IsBase else KChildShape
    return {
        "ClassVersion": 1,
        "ViewLongA": LongA,
        "ViewLongB": ViewStyle(Planned, IsBase),
        "ViewLongC": 0,
        "ViewFlags": Flags,
        "ViewLongD": 100,
        "ViewLongE": 0,
        "ViewRepKey": HandleNumber(KeySet.ViewRep),
        "ViewFlagA": 1,
        "BodyCount": 1,
        "Bodies": (ViewBody(Source, Edges),),
        **TrailFields(KeySet, Planned, Source),
    }


# sight needs an explicit validity boundary so projected geometry retains its paper and model relationships
def Sight(Planned: ViewPlan) -> KPointTriple:
    Delta = [
        Target - EyeAxis
        for Target, EyeAxis in zip(Planned.TargetPoint, Planned.EyePoint)
    ]
    Length = SquareRoot(sum(Piece * Piece for Piece in Delta))
    if Length <= 0:
        raise ValueError("Authored DWG view has no viewing direction")
    return (Delta[0] / Length, Delta[1] / Length, Delta[2] / Length)


# the eed operation needs a consistent construction rule so projected geometry retains its paper and model relationships
def MakeEed(AppName: str, *GroupItems: tuple[str, KDraftValue]) -> DraftEed:
    return DraftEed(HardPointer("APPID:" + AppName), DraftRecord(GroupItems))


# the layout eed contract needs a shared interpretation so projected geometry retains its paper and model relationships
def LayoutEed(Family: tuple[tuple[ViewKeys, ViewPlan], ...]) -> DraftEed:
    Items: list[tuple[str, KDraftValue]] = [("1070", 1), ("1071", 0)]
    Items.append(("1071", len(Family)))
    for KeySet, Planned in Family:
        Items += [("1071", 0), ("1071", HandleNumber(KeySet.ViewRep))]
        Items += [("1040", Value) for Value in (*Sight(Planned), *Planned.Frame.Up)]
    return MakeEed("AUTO_VIEW_XDATA", *Items)


# the nest eed contract needs a shared interpretation so projected geometry retains its paper and model relationships
def NestEed(Planned: ViewPlan, Parent: ViewPlan | None) -> DraftEed:
    Across, Upward = Planned.Center
    if Parent is not None:
        Across, Upward = Across - Parent.Center[0], Upward - Parent.Center[1]
    return MakeEed(
        "AUTO_NEST_XDATA",
        ("1070", 1),
        ("1070", 0 if Parent else 1),
        ("1040", Across),
        ("1040", Upward),
    )


# the view rep eed contract needs a shared interpretation so projected geometry retains its paper and model relationships
def ViewRepEed(
    Planned: ViewPlan,
    Parent: ViewPlan | None,
    Family: tuple[tuple[ViewKeys, ViewPlan], ...],
) -> tuple[DraftEed, ...]:
    Marks = (
        MakeEed("ACAD_CENTERMARK_INFO_ID", ("1071", 47), ("1040", 0.0), ("1040", 0.0)),
        MakeEed("ACAD_CENTERLINE_INFO_ID", ("1071", 15)),
    )
    if Parent is not None:
        return (*Marks, NestEed(Planned, Parent))
    Scale = MakeEed("AUTO_SCALE_XDATA", ("1070", 1), ("1040", Planned.Frame.ViewScale))
    return (LayoutEed(Family), *Marks, Scale, NestEed(Planned, None))


# the view rep operation needs a consistent construction rule so projected geometry retains its paper and model relationships
def PlaceViewRepMut(
    Ledger: DraftBook,
    KeySet: ViewKeys,
    Planned: ViewPlan,
    Parent: ViewPlan | None,
    Family: tuple[tuple[ViewKeys, ViewPlan], ...],
    Source: ViewSource,
    Edges: tuple[DraftRecord, ...],
) -> str:
    return PlaceMut(
        Ledger,
        KeySet.ViewRep,
        "ACDBVIEWREP",
        {
            "ReactorCount": 0,
            "NoXdic": 0,
            "HasDsData": 0,
            "Owner": SoftPointer(KeySet.Body),
            "Reactors": (),
            "Xdic": HardOwner(KeySet.ViewRep + "/Xdic"),
        },
        ViewFields(KeySet, Planned, Parent is None, Source, Edges),
        ViewRepEed(Planned, Parent, Family),
    )
