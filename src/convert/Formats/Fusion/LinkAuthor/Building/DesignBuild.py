from convert.Formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.Formats.Fusion.LinkAuthor.Model.AssemblyPlan import AssemblyPlan
from convert.Formats.Fusion.LinkAuthor.Model.AssemblySpec import AssemblySpec
from convert.Formats.Fusion.LinkAuthor.Model.RootFacts import RootFacts
from convert.Formats.Fusion.LinkAuthor.Model.TargetFacts import TargetFacts
from convert.Formats.Fusion.LinkAuthor.Records.JointRecords import (
    JointRecords,
    JointSide,
)
from convert.Formats.Fusion.LinkAuthor.Records.LinkGuids import KXRefManager
from convert.Formats.Fusion.LinkAuthor.Records.OccurRecords import OccurRecords
from convert.Formats.Fusion.LinkAuthor.Records.PinRecords import PinRecords
from convert.Formats.Fusion.LinkAuthor.Records.PlaceRecords import PlaceRecords
from convert.Formats.Fusion.LinkAuthor.Records.RecordValues import (
    MakeGroup,
    MakeRecord,
)
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# the group operation needs a consistent construction rule so cross document references retain their intended ownership
def PlaceGroup(
    RootInfo: RootFacts,
    Facts: tuple[TargetFacts, ...],
    Request: AssemblySpec,
    Scheme: AssemblyPlan,
    Index: int,
) -> tuple[EntityRecord, ...]:
    Placement, KeySet, Pinning = (
        Request.Placements[Index],
        Scheme.Places[Index],
        Scheme.Pins[Index],
    )
    Target, Linkage = Facts[Placement.TargetIndex], Scheme.Links[Placement.TargetIndex]
    Records = PlaceRecords(
        RootInfo, Target, Linkage, KeySet, Placement.Matrix, Index == 0
    )
    Records += OccurRecords(
        RootInfo,
        Target,
        KeySet,
        Placement.Matrix,
        None if Pinning is None else Pinning.Feature,
    )
    if Pinning is not None:
        Records += PinRecords(RootInfo, Target, Linkage, KeySet, Pinning)
    return Records


# the joint group contract needs a stable decomposition so cross document references retain their intended ownership
def JointGroup(
    RootInfo: RootFacts,
    Facts: tuple[TargetFacts, ...],
    Request: AssemblySpec,
    Scheme: AssemblyPlan,
) -> tuple[EntityRecord, ...]:
    if Request.Joint is None or Scheme.Joint is None:
        return ()
    Sides = tuple(
        JointSide(
            Facts[Request.Placements[Index].TargetIndex],
            Scheme.Places[Index],
            Request.Placements[Index].Matrix,
            Scheme.Pins[Index] is not None,
        )
        for Index in (Request.Joint.FirstIndex, Request.Joint.SecondIndex)
    )
    return JointRecords(RootInfo, Sides[0], Sides[1], Scheme.Joint)


# the design records contract needs a shared interpretation so cross document references retain their intended ownership
def DesignRecords(
    RootInfo: RootFacts,
    Facts: tuple[TargetFacts, ...],
    Request: AssemblySpec,
    Scheme: AssemblyPlan,
) -> tuple[EntityRecord, ...]:
    Manager = MakeRecord(
        Scheme.XRefId,
        MakeGroup(
            KXRefManager,
            ("isXRefReadonly", True),
            ("rOwnerComponent", LocalRef(RootInfo.Component)),
        ),
    )
    Placed = tuple(
        Record
        for Index in range(len(Request.Placements))
        for Record in PlaceGroup(RootInfo, Facts, Request, Scheme, Index)
    )
    return (Manager, *Placed, *JointGroup(RootInfo, Facts, Request, Scheme))
