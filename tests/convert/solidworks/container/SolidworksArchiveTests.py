# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import json as JsonLib
from pathlib import Path as FilePath
import struct as StructLib
from typing import TypedDict
import pytest as PytestLib
from convert.adapters.solidworks.container.Archive import (
    CLASS_REFERENCE_KIND as KindInfo,
    ClassLayout,
    DEFINITION_KIND as KindInfoA,
    IsLayoutObject,
    IsLayoutSeq,
    KLayoutObject,
    LayoutTable,
    KLayoutValue,
    STREAM_HEADER_SIZE as SizeInfo,
    SegmentationError,
    StaticSegment,
    build_model as BuildModel,
    container_mo_version as ContainerMoVersion,
    resolve_base as ResolveBase,
    segment as Segment,
    verify as Verify,
)
from convert.adapters.solidworks.container.Container import (
    SldprtArchive,
)
from convert.adapters.solidworks.container.Format import (
    RESOLVED_FEATURES_STREAM as Stream,
)
from tests.convert.solidworks.core.SolidworksDonorVersion import GetDonorVer


# preserves recorded archive segmentation with fields required by reconstruction checks
class SegmentRecord(TypedDict):
    index: int
    offset: int
    header: int
    end: int
    kind: str
    tag: int
    class_name: str
    class_index: int
    object_index: int
    depth: int
    parent: int
    map_index: int


# keeps recorded fixture metadata concrete after untyped json decoding
class RecordedArchive(TypedDict):
    part: str
    stream_length: int
    base_map_index: int
    object_count: int
    segments: list[SegmentRecord]


# centralizes shared evidence so every related assertion uses one value
KRootInfo = FilePath(__file__).parents[4]

# centralizes shared evidence so every related assertion uses one value
KLayouts = KRootInfo / "re" / "data" / "Layouts" / "ClassLayouts.json"

# centralizes shared evidence so every related assertion uses one value
KSegments = KRootInfo / "re" / "data" / "segments"

# centralizes shared evidence so every related assertion uses one value
KDonors = KRootInfo / "examples" / "Fixtures" / "SolidWorks" / "donors"

# centralizes shared evidence so every related assertion uses one value
KLabels = (
    "baseline",
    "circle",
    "cutbase",
    "padplane",
    "planetop",
    "three",
    "twopad",
    "vendor_cojinete",
    "vendor_ring",
)

# centralizes shared evidence so every related assertion uses one value
KIdentically = 17

# centralizes shared evidence so every related assertion uses one value
KFloor = 54

# centralizes shared evidence so every related assertion uses one value
KFloorA = 18761

# centralizes shared evidence so every related assertion uses one value
KSeedInfo = 109


# keeps this focused behavior isolated so regressions remain immediately visible
def Layouts() -> LayoutTable:
    return LayoutTable.load(KLayouts)


# rejects malformed recorded json before fixture reconstruction consumes its fields
def RecordedString(Payload: KLayoutObject, KeyValue: str) -> str:
    Value = Payload.get(KeyValue)
    if not isinstance(Value, str):
        raise TypeError(f"recorded archive field {KeyValue!r} must be a string")
    return Value


# rejects malformed recorded json before numeric offsets enter archive operations
def RecordedInteger(Payload: KLayoutObject, KeyValue: str) -> int:
    Value = Payload.get(KeyValue)
    if not isinstance(Value, int) or isinstance(Value, bool):
        raise TypeError(f"recorded archive field {KeyValue!r} must be an integer")
    return Value


# converts each json segment into the concrete record used by static reconstruction
def RecordedSegment(Value: KLayoutValue) -> SegmentRecord:
    if not IsLayoutObject(Value):
        raise TypeError("recorded archive segment must be an object")
    return {
        "index": RecordedInteger(Value, "index"),
        "offset": RecordedInteger(Value, "offset"),
        "header": RecordedInteger(Value, "header"),
        "end": RecordedInteger(Value, "end"),
        "kind": RecordedString(Value, "kind"),
        "tag": RecordedInteger(Value, "tag"),
        "class_name": RecordedString(Value, "class_name"),
        "class_index": RecordedInteger(Value, "class_index"),
        "object_index": RecordedInteger(Value, "object_index"),
        "depth": RecordedInteger(Value, "depth"),
        "parent": RecordedInteger(Value, "parent"),
        "map_index": RecordedInteger(Value, "map_index"),
    }


# keeps this focused behavior isolated so regressions remain immediately visible
def Recorded(Label: str) -> RecordedArchive:
    TargetPath = KSegments / f"segments_{Label}.json"
    if not TargetPath.is_file():
        PytestLib.skip(f"no recorded segmentation for {Label}")
    RawPayload: object = JsonLib.loads(TargetPath.read_text(encoding="utf-8"))
    if not IsLayoutObject(RawPayload):
        raise TypeError(f"recorded archive {TargetPath} must be a json object")
    RawSegments = RawPayload.get("segments")
    if not IsLayoutSeq(RawSegments):
        raise TypeError(f"recorded archive {TargetPath} must contain a segments list")
    return {
        "part": RecordedString(RawPayload, "part"),
        "stream_length": RecordedInteger(RawPayload, "stream_length"),
        "base_map_index": RecordedInteger(RawPayload, "base_map_index"),
        "object_count": RecordedInteger(RawPayload, "object_count"),
        "segments": [RecordedSegment(Value) for Value in RawSegments],
    }


# keeps this focused behavior isolated so regressions remain immediately visible
def RecordedPart(Payload: RecordedArchive) -> tuple[bytes, int | None]:
    PartDoc = FilePath(Payload["part"])
    if not PartDoc.is_file():
        PytestLib.skip(f"traced part {PartDoc} is not present in this checkout")
    Archive = SldprtArchive.from_bytes(PartDoc.read_bytes())
    BlobInfo = Archive.streams[Stream]
    assert len(BlobInfo) == Payload["stream_length"]
    return (BlobInfo, ContainerMoVersion(Archive.streams))


# keeps this focused behavior isolated so regressions remain immediately visible
def AuthoredMV() -> int | None:
    Found: set[int] = set()
    for Label in KLabels:
        if Label.startswith("vendor_"):
            continue
        TargetPath = KSegments / f"segments_{Label}.json"
        if not TargetPath.is_file():
            continue
        PartDoc = FilePath(Recorded(Label)["part"])
        if not PartDoc.is_file():
            continue
        Version = ContainerMoVersion(
            SldprtArchive.from_bytes(PartDoc.read_bytes()).streams
        )
        if Version is not None:
            Found.add(Version)
    if len(Found) != 1:
        return None
    return Found.pop()


# keeps this focused behavior isolated so regressions remain immediately visible
def StaticSegments(
    BlobInfo: bytes, Payload: RecordedArchive
) -> tuple[StaticSegment, ...]:
    RowsInfo: list[StaticSegment] = []
    for ItemValue in Payload["segments"]:
        Offset = ItemValue["offset"]
        Schema = (
            StructLib.unpack_from("<H", BlobInfo, Offset + 2)[0]
            if ItemValue["kind"] == KindInfoA
            else 0
        )
        RowsInfo.append(
            StaticSegment(
                index=ItemValue["index"],
                offset=Offset,
                header=ItemValue["header"],
                end=ItemValue["end"],
                kind=ItemValue["kind"],
                token=ItemValue["tag"],
                wide=False,
                schema=Schema,
                class_name=ItemValue["class_name"],
                class_index=ItemValue["class_index"],
                object_index=ItemValue["object_index"],
                depth=ItemValue["depth"],
                parent=ItemValue["parent"],
            )
        )
    return tuple(RowsInfo)


# keeps this focused behavior isolated so regressions remain immediately visible
def DonorStreams() -> tuple[tuple[str, bytes], ...]:
    RowsInfo: list[tuple[str, bytes]] = []
    for Donor in sorted(KDonors.iterdir()):
        StreamA = Donor / "resolved.bin"
        if StreamA.is_file():
            RowsInfo.append((Donor.name, StreamA.read_bytes()))
    return tuple(RowsInfo)


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize("Label", KLabels)
def TestRSRTBI(Label: str) -> None:
    Payload = Recorded(Label)
    BlobInfo = RecordedPart(Payload)[0]
    Segments = StaticSegments(BlobInfo, Payload)
    ModelDoc = BuildModel(
        BlobInfo, Segments, Payload["base_map_index"], Segments[0].offset
    )
    assert len(ModelDoc.nodes) == Payload["object_count"]
    assert ModelDoc.emit() == BlobInfo


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize("Label", KLabels)
def TestSSAWTRO(Label: str) -> None:
    Payload = Recorded(Label)
    BlobInfo, Version = RecordedPart(Payload)
    LayoutsA = Layouts()
    Expected = [ItemValue["offset"] for ItemValue in Payload["segments"]]
    Header = Payload["segments"][0]["offset"]
    try:
        Produced = Segment(
            BlobInfo,
            Payload["base_map_index"],
            LayoutsA,
            header_size=Header,
            mo_version=Version,
        )
        Reached = [ItemValue.offset for ItemValue in Produced]
    except SegmentationError as Failure:
        Reached = [ItemValue.offset for ItemValue in Failure.reached]
        assert Failure.offset in Expected, (Label, Failure.offset)
    assert Reached
    assert Reached == Expected[: len(Reached)], Label


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize("Label", KLabels)
def TestRSMTCR(Label: str) -> None:
    Payload = Recorded(Label)
    BaseInfo = Payload["base_map_index"]
    Counter = BaseInfo
    for ItemValue in Payload["segments"]:
        assert ItemValue["map_index"] == Counter, (Label, ItemValue["offset"])
        if ItemValue["kind"] == KindInfoA:
            Counter += 2
        elif ItemValue["kind"] == KindInfo:
            Counter += 1


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize("Label", KLabels)
def TestRPCARDV(Label: str) -> None:
    Payload = Recorded(Label)
    Version = RecordedPart(Payload)[1]
    assert Version == (14000 if Label.startswith("vendor_") else 18000), Label


# keeps this focused behavior isolated so regressions remain immediately visible
def AssertLayoutRow(NameText: str, Entry: ClassLayout) -> None:
    assert Entry.confidence in {"confirmed", "partial", "not found"}
    assert Entry.source
    assert set(Entry.runs_by_version) <= set(Entry.run_keys()), NameText
    for LookupKey, Gated in Entry.runs_by_version.items():
        assert Gated, (NameText, LookupKey)
        for Version, Length in Gated.items():
            assert Version > 0, (NameText, LookupKey)
            assert Length >= 0, (NameText, LookupKey)
    if Entry.confidence == "confirmed":
        assert not Entry.repeats
        for LookupKey in Entry.run_keys():
            Elements = Entry.variable_runs.get(LookupKey, ())
            assert LookupKey in Entry.constant_run_keys or Elements, (
                NameText,
                LookupKey,
            )
            assert all((Element.rule != "opaque" for Element in Elements)), (
                NameText,
                LookupKey,
            )
    for SlotInfo, Elements in Entry.variable_runs.items():
        assert Elements
        assert SlotInfo in set(Entry.run_keys()) | {"lead"}
        for Element in Elements:
            assert Element.rule in {"string", "count", "conditional", "guard", "opaque"}


# keeps this focused behavior isolated so regressions remain immediately visible
def GetRecordedSet() -> set[str]:
    RecordedNames = set[str]()
    for Label in KLabels:
        TargetPath = KSegments / f"segments_{Label}.json"
        if not TargetPath.is_file():
            continue
        for ItemValue in Recorded(Label)["segments"]:
            if ItemValue["kind"] in {KindInfoA, KindInfo}:
                RecordedNames.add(ItemValue["class_name"])
    return RecordedNames


# keeps this focused behavior isolated so regressions remain immediately visible
def TestSLTMTRC() -> None:
    LayoutsA = Layouts()
    assert LayoutsA.version == 1
    Confirmed = [
        NameText
        for NameText, Entry in LayoutsA.classes.items()
        if Entry.confidence == "confirmed"
    ]
    assert len(Confirmed) >= KFloor
    for NameText, Entry in LayoutsA.classes.items():
        AssertLayoutRow(NameText, Entry)
    assert GetRecordedSet() <= set(LayoutsA.classes)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestFVCDNR() -> None:
    LayoutsA = Layouts()
    Streams = DonorStreams()
    assert len(Streams) == 32
    Version = GetDonorVer(KDonors, AuthoredMV())
    Identical = 0
    for NameText, BlobInfo in Streams:
        Features = DonorFC(NameText)
        SeedInfo = KSeedInfo + Features - 1 if Features > 0 else KSeedInfo
        Resolution = ResolveBase(
            BlobInfo, SeedInfo, LayoutsA, header_size=SizeInfo, mo_version=Version
        )
        Report = Verify(
            BlobInfo,
            Resolution.base,
            LayoutsA,
            header_size=SizeInfo,
            mo_version=Version,
        )
        if Report.identical:
            Identical += 1
    assert Identical >= KIdentically


# keeps this focused behavior isolated so regressions remain immediately visible
def DonorFC(NameText: str) -> int:
    MetaInfo = KDonors / NameText / "meta.json"
    if not MetaInfo.is_file():
        return -1
    RawMeta: object = JsonLib.loads(MetaInfo.read_text(encoding="utf-8"))
    if not IsLayoutObject(RawMeta):
        return -1
    Features = RawMeta.get("features")
    return len(Features) if IsLayoutSeq(Features) else -1


# keeps this focused behavior isolated so regressions remain immediately visible
def TestFORDNR() -> None:
    LayoutsA = Layouts()
    Version = GetDonorVer(KDonors, AuthoredMV())
    Reached = 0
    for NameText, BlobInfo in DonorStreams():
        Features = DonorFC(NameText)
        SeedInfo = KSeedInfo + Features - 1 if Features > 0 else KSeedInfo
        Resolution = ResolveBase(
            BlobInfo, SeedInfo, LayoutsA, header_size=SizeInfo, mo_version=Version
        )
        Report = Verify(
            BlobInfo,
            Resolution.base,
            LayoutsA,
            header_size=SizeInfo,
            mo_version=Version,
        )
        assert Report.object_count > 0, NameText
        Reached += Report.object_count
    assert Reached >= KFloorA


# keeps this focused behavior isolated so regressions remain immediately visible
def TestRECCMR() -> None:
    LayoutsA = Layouts()
    Resolved = {
        NameText: Entry
        for NameText, Entry in LayoutsA.classes.items()
        if Entry.source == "re/data/Layouts/ExternalClasses.json"
    }
    assert Resolved
    for NameText, Entry in Resolved.items():
        assert not Entry.repeats, NameText
        for LookupKey in Entry.run_keys():
            Elements = Entry.variable_runs.get(LookupKey, ())
            assert LookupKey in Entry.constant_run_keys or Elements, (
                NameText,
                LookupKey,
            )
            for Element in Elements:
                assert Element.rule != "opaque", (NameText, LookupKey)
    Aliases = {NameText for NameText in Resolved if NameText.startswith("external#")}
    assert Aliases
    for Alias in Aliases:
        assert LayoutsA.classes[Alias].child_slots == Resolved[Alias].child_slots


# keeps this focused behavior isolated so regressions remain immediately visible
def TestFSFNTBC() -> None:
    LayoutsA = Layouts()
    Version = GetDonorVer(KDonors, AuthoredMV())
    for NameText, BlobInfo in DonorStreams():
        Report = Verify(
            BlobInfo, 109, LayoutsA, header_size=SizeInfo, mo_version=Version
        )
        if Report.identical:
            continue
        assert Report.blocking_class, NameText
        assert Report.blocking_slot, NameText
        assert Report.blocking_offset >= SizeInfo, NameText
        assert (
            Report.blocking_class in LayoutsA.classes
            or Report.blocking_class.startswith("external#")
            or Report.blocking_class == "<stream>"
        ), NameText
