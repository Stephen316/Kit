from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.formats.Fusion.EntityCodec.Model.ValueMap import ValueMap
from convert.formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.LinkAuthor.Edits.RecordEdit import (
    AppendItems,
    ReadValue,
    WriteValue,
)
from convert.formats.Fusion.LinkAuthor.Model.AssemblyPlan import AssemblyPlan
from convert.formats.Fusion.LinkAuthor.Model.AssemblySpec import AssemblySpec
from convert.formats.Fusion.LinkAuthor.Model.RootFacts import RootFacts
from convert.formats.Fusion.LinkAuthor.Model.TargetFacts import TargetFacts
from convert.formats.Fusion.LinkAuthor.Records.EntryRecord import EntryRecord
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


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
