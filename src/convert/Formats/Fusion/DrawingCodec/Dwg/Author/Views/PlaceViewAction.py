from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.DraftLinks import (
    HardOwner,
    SoftPointer,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.PlaceMut import PlaceMut
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlaceFolder import (
    PlaceFolderMut,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlaceRecord import (
    ByteGroups,
    PlaceRecordMut,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Edges.SolidParts import SolidShape
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Edges.ViewEdges import ViewEdges
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Spec.ViewSource import ViewSource
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Views.PlaceAction import (
    PlaceActionMut,
    PlaceDependMut,
    PlaceParamMut,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Views.PlaceEdges import (
    PlaceEdgesMut,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Views.ViewKeys import ViewKeys
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Views.ViewPlan import ViewPlan
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Views.ViewRepData import (
    PlaceViewRepMut,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Author.Views.ViewState import ViewState

# round trip must remain consistent across callers so projected geometry retains its paper and model relationships
KRoundTrip = "ACAD_XREC_ROUNDTRIP"


# the parameters operation needs a consistent construction rule so projected geometry retains its paper and model relationships
def PlaceParamsMut(
    Ledger: DraftBook, KeySet: ViewKeys, IsProjected: bool
) -> tuple[str, ...]:
    Action = KeySet.Action
    Params = [
        PlaceParamMut(
            Ledger,
            Action + "/BorderParam",
            "ACDBASSOCVIEWBORDERACTIONPARAM",
            Action,
            Action + "/Border",
        ),
        PlaceParamMut(
            Ledger,
            Action + "/ObjectParam",
            "ACDBASSOCOBJECTACTIONPARAM",
            Action,
            Action + "/Block",
        ),
    ]
    if IsProjected:
        Params.append(
            PlaceParamMut(
                Ledger,
                Action + "/RepParam",
                "ACDBASSOCVIEWREPACTIONPARAM",
                Action,
                Action + "/Parent",
            )
        )
    Params.append(
        PlaceParamMut(
            Ledger, Action + "/Hatch", "ACDBASSOCVIEWREPHATCHMANAGER", Action, ""
        )
    )
    return tuple(Params)


# the state operation needs a consistent construction rule so projected geometry retains its paper and model relationships
def PlaceStateMut(
    Ledger: DraftBook, KeySet: ViewKeys, Planned: ViewPlan, Source: ViewSource
) -> None:
    Folder = KeySet.ViewRep + "/Xdic"
    Record = PlaceFolderMut(Ledger, Folder, KeySet.ViewRep, True, KRoundTrip)
    Payload = ViewState(
        Planned.TargetPoint,
        Planned.EyePoint,
        Planned.Frame.Up,
        ((Source.GeometryGuid, Source.BoundsMin, Source.BoundsMax),),
    )
    _ = PlaceRecordMut(
        Ledger,
        Record,
        Folder,
        (
            ("102", "ACAD_ROUNDTRIP_2016_ACDBIMPVIEWREP"),
            ("90", 0),
            ("102", "FDOC_VIEW_STATE_CAPTURE"),
            ("90", len(Payload)),
            *ByteGroups(Payload),
        ),
    )


# the family shape must stay shared so drawing view authoring uses one contract for compatible values
KFamily = tuple[tuple[ViewKeys, ViewPlan], ...]


# the view act operation needs a consistent construction rule so projected geometry retains its paper and model relationships
def PlaceViewActMut(
    Ledger: DraftBook,
    KeySet: ViewKeys,
    Planned: ViewPlan,
    Family: KFamily,
    Source: ViewSource,
    Shape: SolidShape,
) -> None:
    Action = KeySet.Action
    Elders = [Member for Member in Family if Member[1].Index == Planned.Parent]
    Parent = Elders[0][0] if Elders else None
    Dependencies = (Action + "/Border", Action + "/Block") + (
        (Action + "/Parent",) if Parent else ()
    )
    Params = PlaceParamsMut(Ledger, KeySet, Parent is not None)
    _ = PlaceActionMut(Ledger, Action, KeySet.Body, Dependencies, Params)
    _ = PlaceDependMut(Ledger, Dependencies[0], Action, 1, KeySet.Drawing, 1)
    _ = PlaceDependMut(Ledger, Dependencies[1], Action, 2, KeySet.ModelRef, 1)
    if Parent:
        _ = PlaceDependMut(Ledger, Action + "/Parent", Action, 3, Parent.Action, 0)
    _ = PlaceMut(
        Ledger,
        KeySet.Body,
        "ACDBASSOCVIEWREPACTIONBODY",
        {"Owner": SoftPointer(Action)},
        {
            "ViewKind": Planned.Frame.ViewKind,
            "ViewAngle": Planned.Frame.ViewAngle,
            "ViewRep": HardOwner(KeySet.ViewRep),
        },
    )
    EdgeRows = ViewEdges(Shape, Planned.Frame, Planned.ShowHidden)
    Edges = PlaceEdgesMut(Ledger, KeySet, EdgeRows)
    _ = PlaceViewRepMut(
        Ledger, KeySet, Planned, Elders[0][1] if Elders else None, Family, Source, Edges
    )
    Owner = {"Owner": SoftPointer(KeySet.ViewRep)}
    _ = PlaceMut(
        Ledger,
        KeySet.ViewRep + "/Orientation",
        "ACDBVIEWREPORIENTATION",
        Owner,
        {
            "EyePoint": Planned.EyePoint,
            "UpVector": Planned.Frame.Up,
            "TargetPoint": Planned.TargetPoint,
        },
    )
    _ = PlaceMut(
        Ledger, KeySet.ViewRep + "/Definition", "ACDBVIEWREPORIENTATIONDEF", Owner, {}
    )
    PlaceStateMut(Ledger, KeySet, Planned, Source)
