from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Model.ValueObject import ValueObject
from convert.formats.Fusion.EntityCodec.Model.ValuePair import ValuePair
from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.LinkAuthor.Edits.RecordEdit import (
    AddPairs,
    AppendItems,
    ReadValue,
    WriteValue,
)
from convert.formats.Fusion.LinkAuthor.Model.AssemblyPlan import AssemblyPlan
from convert.formats.Fusion.LinkAuthor.Model.AssemblySpec import AssemblySpec
from convert.formats.Fusion.LinkAuthor.Model.RootFacts import RootFacts
from convert.formats.Fusion.LinkAuthor.Model.TargetFacts import TargetFacts
from convert.formats.Fusion.LinkAuthor.Records.ActRecords import ActRecords
from convert.formats.Fusion.LinkAuthor.Records.LinkGuids import KActTableEntry
from convert.formats.Fusion.LinkAuthor.Records.RecordValues import MakeGroup
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


def ActEntries(
    RootInfo: RootFacts, Scheme: AssemblyPlan
) -> tuple[ValueObject[KEntityValue], ...]:
    return tuple(
        ValueObject(
            (
                MakeGroup(
                    KActTableEntry,
                    ("rActData", LocalRef(KeySet.ActData)),
                    ("tgtIdentifier", f"{RootInfo.ActSegment}_{KeySet.ActInstance}"),
                ),
            )
        )
        for KeySet in Scheme.Places
    )


def EntryName(Entry: KEntityValue) -> str:
    if not isinstance(Entry, ValueObject) or len(Entry.Groups) != 1:
        raise ValueError("Fusion ACT table entry is malformed")
    Names = tuple(
        Field.Value
        for Field in Entry.Groups[0].Fields
        if Field.FieldName == "tgtIdentifier" and type(Field.Value) is str
    )
    if len(Names) != 1:
        raise ValueError("Fusion ACT table entry is malformed")
    return str(Names[0])


def ActRecordSet(
    RootInfo: RootFacts,
    Facts: tuple[TargetFacts, ...],
    Request: AssemblySpec,
    Scheme: AssemblyPlan,
) -> tuple[EntityRecord, ...]:
    return tuple(
        Record
        for Placement, KeySet in zip(Request.Placements, Scheme.Places, strict=True)
        for Record in ActRecords(
            RootInfo,
            Facts[Placement.TargetIndex],
            Scheme.Links[Placement.TargetIndex],
            KeySet,
        )
    )


def EditAct(
    Records: tuple[EntityRecord, ...], RootInfo: RootFacts, Scheme: AssemblyPlan
) -> tuple[EntityRecord, ...]:
    Current = ReadValue(Records, RootInfo.ActTable, "ACTTableEntries")
    if not isinstance(Current, ValueSeries):
        raise ValueError("Fusion ACT table entries are malformed")
    Entries = tuple(sorted(Current.Items + ActEntries(RootInfo, Scheme), key=EntryName))
    Instances = tuple(LocalRef(KeySet.ActInstance) for KeySet in Scheme.Places)
    Mapping: tuple[ValuePair[KEntityValue], ...] = tuple(
        ValuePair(KeySet.InstanceId, LocalRef(KeySet.ActInstance))
        for KeySet in reversed(Scheme.Places)
    )
    Tables = tuple(LocalRef(KeySet.ActTable) for KeySet in Scheme.Places)
    Records = WriteValue(
        Records, RootInfo.ActTable, "ACTTableEntries", ValueSeries(Entries)
    )
    Records = AppendItems(Records, RootInfo.ActTable, "refdTables", Tables)
    Records = AppendItems(Records, RootInfo.ActInstances, "children", Instances)
    Records = AddPairs(Records, RootInfo.ActRoot, "instancesMap", Mapping)
    Records = WriteValue(
        Records, RootInfo.ActRoot, "nextInstanceId", Scheme.InstanceNext
    )
    return AppendItems(Records, RootInfo.ActRoot, "rooted", Instances)
