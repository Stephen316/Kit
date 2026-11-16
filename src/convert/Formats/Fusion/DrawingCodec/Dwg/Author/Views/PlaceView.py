from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftLinks import (
    HardOwner,
    HardPointer,
    SoftPointer,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftRow import DraftEed
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import DraftRecord
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.PlaceMut import (
    KDraftFields,
    AppendMut,
    PlaceMut,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlaceBlock import (
    OwnMut,
    PlaceBlockMut,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlacePort import (
    PlacePortMut,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetKeys import (
    KModelOwned,
    KPaperSpace,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.SlotFields import ReactorSlot
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Views.ViewFrame import TwistAngle
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Views.ViewKeys import (
    MakeKeys,
    ViewKeys,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Views.ViewPlan import ViewPlan

# frame flags must remain consistent across callers so projected geometry retains its paper and model relationships
KFrameFlags = 966656

# port flags must remain consistent across callers so projected geometry retains its paper and model relationships
KPortFlags = 835584


# the synergy eed contract needs a shared interpretation so projected geometry retains its paper and model relationships
def SynergyEed() -> tuple[DraftEed, ...]:
    return (DraftEed(HardPointer("APPID:AcSynergy"), DraftRecord((("1070", 1),))),)


# the blocks operation needs a consistent construction rule so projected geometry retains its paper and model relationships
def PlaceBlocksMut(Ledger: DraftBook, KeySet: ViewKeys, Planned: ViewPlan) -> None:
    _ = PlaceBlockMut(Ledger, KeySet.Inner, "*S")
    _ = PlaceBlockMut(Ledger, KeySet.Outer, "*S")
    _ = PlaceMut(
        Ledger,
        KeySet.InnerRef,
        "ACDBVIEWREPBLOCKREFERENCE",
        {
            "EntityMode": 0,
            "Owner": SoftPointer(KeySet.Outer),
            **ReactorSlot(Ledger, KeySet.InnerRef),
        },
        {
            "Insertion": Planned.Insertion,
            "BlockHeader": HardPointer(KeySet.Inner),
            "Viewport": SoftPointer(KeySet.Port),
        },
    )
    _ = OwnMut(Ledger, KeySet.Outer, KeySet.InnerRef)
    AppendMut(Ledger, KeySet.Inner + ".Inserts", SoftPointer(KeySet.InnerRef))
    _ = PlaceMut(
        Ledger,
        KeySet.ModelRef,
        "ACDBVIEWREPBLOCKREFERENCE",
        {"EntityMode": 2, **ReactorSlot(Ledger, KeySet.ModelRef)},
        {
            "Insertion": (0.0, 0.0, 0.0),
            "BlockHeader": HardPointer(KeySet.Outer),
            "Viewport": SoftPointer(KeySet.Port),
        },
    )
    AppendMut(Ledger, KModelOwned, HardOwner(KeySet.ModelRef))
    AppendMut(Ledger, KeySet.Outer + ".Inserts", SoftPointer(KeySet.ModelRef))


# the ports operation needs a consistent construction rule so projected geometry retains its paper and model relationships
def PlacePortsMut(Ledger: DraftBook, KeySet: ViewKeys, Planned: ViewPlan) -> None:
    Width, Height = Planned.BorderSize
    Center = (*Planned.Center, 0.0)
    Plane: KDraftFields = {"Center": Center, "Width": Width, "Height": Height}
    _ = PlacePortMut(
        Ledger,
        KeySet.Frame,
        {"NoXdic": 1, "Invisible": 1, **ReactorSlot(Ledger, KeySet.Frame)},
        {
            **Plane,
            "ViewTarget": (0.0, 0.0, 0.0),
            "ViewDirection": (0.0, 0.0, 1.0),
            "TwistAngle": 0.0,
            "ViewHeight": Height,
            "ViewCenter": (0.0, 0.0),
            "StatusFlags": KFrameFlags,
            "UcsAtOrigin": 1,
            "UcsOrigin": (0.0, 0.0, 0.0),
            "UcsXAxis": (1.0, 0.0, 0.0),
            "UcsYAxis": (0.0, 1.0, 0.0),
        },
        SynergyEed(),
    )
    _ = PlacePortMut(
        Ledger,
        KeySet.Port,
        {"NoXdic": 1, "Invisible": 1, **ReactorSlot(Ledger, KeySet.Port)},
        {
            **Plane,
            "ViewTarget": Planned.Target,
            "ViewDirection": Planned.Frame.Eye,
            "TwistAngle": TwistAngle(Planned.Frame),
            "ViewHeight": Height / Planned.Frame.ViewScale,
            "ViewCenter": (0.0, 0.0),
            "StatusFlags": KPortFlags,
            "UcsAtOrigin": 1,
            "UcsOrigin": Planned.Target,
            "UcsXAxis": Planned.Frame.Right,
            "UcsYAxis": Planned.Frame.Up,
        },
        SynergyEed(),
    )


# the drawing operation needs a consistent construction rule so projected geometry retains its paper and model relationships
def PlaceDrawingMut(
    Ledger: DraftBook, KeySet: ViewKeys, Planned: ViewPlan, ScaleKey: str
) -> None:
    Width, Height = Planned.BorderSize
    Across, Upward = Planned.Center
    _ = PlaceMut(
        Ledger,
        KeySet.Drawing,
        "DRAWINGVIEW",
        ReactorSlot(Ledger, KeySet.Drawing),
        {
            "BorderMin": (Across - Width / 2, Upward - Height / 2),
            "BorderMax": (Across + Width / 2, Upward + Height / 2),
            "ViewScale": Planned.Frame.ViewScale,
            "ViewCenter": Planned.Center,
            "Viewport": SoftPointer(KeySet.Port),
            "ScaleObject": HardPointer(ScaleKey),
        },
    )
    _ = OwnMut(Ledger, KPaperSpace, KeySet.Drawing)


# the view operation needs a consistent construction rule so projected geometry retains its paper and model relationships
def PlaceViewMut(Ledger: DraftBook, Planned: ViewPlan, ScaleKey: str) -> ViewKeys:
    KeySet = MakeKeys(Planned.Index)
    PlaceBlocksMut(Ledger, KeySet, Planned)
    PlacePortsMut(Ledger, KeySet, Planned)
    PlaceDrawingMut(Ledger, KeySet, Planned, ScaleKey)
    return KeySet
