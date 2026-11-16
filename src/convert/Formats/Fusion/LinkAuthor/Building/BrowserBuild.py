from convert.Formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.Formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.Formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.Formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.Formats.Fusion.LinkAuthor.Edits.RecordEdit import (
    AppendItems,
    ReadValue,
    WriteValue,
)
from convert.Formats.Fusion.LinkAuthor.Model.AssemblyPlan import AssemblyPlan
from convert.Formats.Fusion.LinkAuthor.Model.AssemblySpec import AssemblySpec
from convert.Formats.Fusion.LinkAuthor.Model.RootFacts import RootFacts
from convert.Formats.Fusion.LinkAuthor.Model.TargetFacts import TargetFacts
from convert.Formats.Fusion.LinkAuthor.Records.EntryRecord import EntryRecord
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# the browser set contract needs a shared interpretation so cross document references retain their intended ownership
def BrowserSet(
    RootInfo: RootFacts,
    Facts: tuple[TargetFacts, ...],
    Request: AssemblySpec,
    Scheme: AssemblyPlan,
) -> tuple[EntityRecord, ...]:
    return tuple(
        EntryRecord(
            RootInfo,
            Facts[Placement.TargetIndex],
            Scheme.Links[Placement.TargetIndex],
            KeySet,
        )
        for Placement, KeySet in zip(Request.Placements, Scheme.Places, strict=True)
    )


# edit browser needs an explicit validity boundary so cross document references retain their intended ownership
def EditBrowser(
    Records: tuple[EntityRecord, ...], RootInfo: RootFacts, Scheme: AssemblyPlan
) -> tuple[EntityRecord, ...]:
    Current = ReadValue(Records, RootInfo.BrowserRoot, "passiveentries")
    if not isinstance(Current, ValueMap):
        raise ValueError("Fusion browser entry map is malformed")
    Added: tuple[ValuePair[KEntityValue], ...] = tuple(
        ValuePair(
            SegmentRef(KeySet.Instance, RootInfo.DesignSegment),
            LocalRef(KeySet.EntryId),
        )
        for KeySet in Scheme.Places
    )
    Records = WriteValue(
        Records,
        RootInfo.BrowserRoot,
        "passiveentries",
        ValueMap(Current.Entries + Added),
    )
    return AppendItems(
        Records,
        RootInfo.RootEntry,
        "children",
        tuple(LocalRef(KeySet.EntryId) for KeySet in Scheme.Places),
    )
