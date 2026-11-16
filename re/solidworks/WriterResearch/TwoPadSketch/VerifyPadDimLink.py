# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Replay only the four upper-pad sketch display owner records."""

from argparse import ArgumentParser
from copy import deepcopy as CopyValue
from hashlib import sha256 as ShaValue
from json import dumps as DumpJson
from math import isclose as IsClose
from pathlib import Path as FilePath
from struct import pack as PackFields
import sys

# continued replay uses the same strict sealed discovery source and helper implementations
KRepository = FilePath(__file__).resolve().parents[4]

# declare the existing research owners without product package imports
sys.path[:0] = [
    str(KRepository / Lane)
    for Lane in (
        "src",
        "re/automation",
        "re/automation/TwoPad",
        "re/solidworks/WriterResearch",
        "re/solidworks/WriterResearch/TwoPadRelations",
        "re/solidworks/WriterResearch/TwoPadSupport",
    )
]

from Display.Compose import KDisplayClass
from DisplayFavorite import KFavoriteClass
from OriginSketch import KObjectList, KPointHandle, KSketchClass
from PadGeometry import KSavedPhases
from PadReceipts import ReadPadBytes
from PartArchive import PartArchiveState, PartArchiveWriter
from PilotEvidence import pinned_record as ReadJsonPin
from RectDimDisplay import KSketchHandle
from RectangleCorners import KLineHandle
from RectangleDims import KLengthClass
from ResolvedFolders import KNameClass
from VerifyDiscovery import AuditDiscovery
from VerifyPadCap import KCapturePins
from VerifyPadEqual import OpenPadLines, ReadPadLane, SavePadState
from WritePadDimLink import EncodePadDimLink, KPadDimClasses
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import ArchiveError, EncodeObjectRef
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Sketch.Cursor import SketchArchive
from convert.adapters.solidworks.Sketch.DimHandle import ReadDimHandle
from convert.adapters.solidworks.Sketch.DisplayOpen import ReadDisplayOpen
from convert.adapters.solidworks.Sketch.Displays import (
    ReadDisplays,
    ReadSavedDimEnd,
    TakeShownClass,
)
from convert.adapters.solidworks.Sketch.GeometryTypes import (
    KSketchDistance,
    SketchGeometry,
)
from convert.adapters.solidworks.Sketch.Regions import ReadRegionStart


# the archived role order must also agree with the licensed feature dimension inventory
def CheckNativeDims(Capture: dict, Geometry: SketchGeometry, OwnerName: str) -> None:
    Rows = Geometry["length_dimensions"]
    for PhaseName in KSavedPhases:
        (Feature,) = (
            Value
            for Value in Capture[PhaseName]["feature_tree"]
            if Value["name"] == OwnerName
        )
        Native = Feature["dimensions"]
        RequireArch(
            tuple((Value["name"], Value["driven_state"]) for Value in Native),
            tuple(zip((Value["name"] for Value in Rows), (2, 1, 2, 2), strict=True)),
            "licensed slot order with referenced upper height",
        )
        RequireArch(
            all(
                IsClose(Source["system_value"], Modeled["metres"], rel_tol=1e-12)
                for Source, Modeled in zip(Native, Rows, strict=True)
            ),
            True,
            "licensed physical dimension values",
        )


# the existing typed reader must consume exactly one owner and its full allocation
def VerifyOwner(
    DataValue: bytes,
    Initial: PartArchiveState,
    FinalState: PartArchiveState,
    SketchIndex: int,
    SlotValue: int,
) -> None:
    Cursor = SketchArchive(Initial.Cursor(DataValue, 0))
    TakeShownClass(Cursor, KSketchHandle)
    RequireArch(ReadDimHandle(Cursor, SketchIndex), SlotValue, "exact owner slot")
    RequireArch(Cursor.Offset, len(DataValue), "exact owner return")
    RequireArch(SavePadState(Cursor), FinalState, "complete owner allocation")


# follow the surrounding display records while constructing only the compact owner link
def ReplayDimLink(Directory: FilePath, Capture: dict) -> dict[str, object]:
    SaveValue = Capture["save"]
    Archive = SldprtArchive.from_bytes(
        ReadPadBytes(Directory, SaveValue["file"], SaveValue["sha256"])
    )
    Resolved = Archive.require("Contents/Config-0-ResolvedFeatures")
    Cursor, Geometry, OwnerName = OpenPadLines(
        Archive.require("Contents/Config-0"), Resolved
    )
    ReadPadLane(Cursor, Geometry)
    CheckNativeDims(Capture, Geometry, OwnerName)
    SketchIndex = Geometry["object_index"]
    Whole = SketchArchive(SavePadState(Cursor).Cursor(Resolved, Cursor.Offset))
    ReadDisplays(Whole, Geometry)
    TakeShownClass(Cursor, KObjectList)
    RequireArch(Cursor.ReadInts("<H"), (4,), "four licensed display owners")
    Records: list[dict[str, object]] = []
    for SlotValue, DimValue in enumerate(Geometry["length_dimensions"]):
        TakeShownClass(Cursor, KDisplayClass)
        Visual = FieldCursor(Resolved, Cursor.Offset)
        Visual.ReadInts("<4H")
        VisualIndex = Visual.ReadValue("<2i2HBIHhf2Hi")[-1]
        RequireArch(VisualIndex, SlotValue + 12, "ordered saved visual index")
        ReadDisplayOpen(Cursor, True)
        Start = Cursor.Offset
        Initial = SavePadState(Cursor)
        TakeShownClass(Cursor, KSketchHandle)
        RequireArch(
            ReadDimHandle(Cursor, SketchIndex), SlotValue, "actual saved handle owner"
        )
        Observed = SavePadState(Cursor)
        DimId = DimValue["native_id"]
        DataValue, FinalState = EncodePadDimLink(
            KConfigGen, Initial, Geometry, SlotValue, DimId
        )
        RequireArch(
            DataValue == Resolved[Start : Cursor.Offset],
            True,
            "exact saved owner slice",
        )
        RequireArch(FinalState, Observed, "same complete saved handle state")
        VerifyOwner(DataValue, Initial, FinalState, SketchIndex, SlotValue)
        ReadSavedDimEnd(Cursor, DimValue["metres"])
        Records.append(
            {
                "slot": SlotValue,
                "visual_index": VisualIndex,
                "sketch_slot": SketchIndex,
                "dimension_id": DimId,
                "name": DimValue["name"],
                "record_bytes": len(DataValue),
                "record_sha256": ShaValue(DataValue).hexdigest(),
                "allocations": [Initial.NextIndex, FinalState.NextIndex],
            }
        )
    RequireArch(Cursor.Offset, Whole.Offset, "same display list return")
    RequireArch(
        SavePadState(Cursor), SavePadState(Whole), "same whole display list state"
    )
    ReadRegionStart(Cursor)
    return {"archive_sha256": SaveValue["sha256"], "owners": Records}


# distinct earlier and current sketch islands make fresh alias changes observable
def BuildDimTrial() -> tuple[PartArchiveState, SketchGeometry, int]:
    Writer = PartArchiveWriter()
    Writer.BeginObject(KSketchClass, 1)
    Earlier = Writer.next_index - 1
    for Name in (
        KObjectList,
        KDisplayClass,
        KSketchHandle,
        KFavoriteClass,
        KLineHandle,
        KPointHandle,
        KLengthClass,
        KNameClass,
        KPadDimClasses[0],
    ):
        Writer.BeginObject(Name, 1)
    Writer.BeginObject(KSketchClass, 1)
    Current = Writer.next_index - 1
    Rows: list[KSketchDistance] = []
    PointIds = [(Index, Index + 11) for Index in range(5)]
    for SlotValue, (Identity, Metres, Operands) in enumerate(
        (
            (81, 0.023, (0, 3)),
            (84, 0.023, (0, 2)),
            (88, 0.004, (4, 0)),
            (101, 0.007, (4, 0)),
        )
    ):
        ClassName = KPadDimClasses[SlotValue]
        for Name in (ClassName, KLengthClass, KNameClass, KPointHandle, KPointHandle):
            Writer.BeginObject(Name, 1)
        Rows.append(
            {
                "class": ClassName,
                "native_id": Identity,
                "name": f"fresh_{Identity}",
                "metres": Metres,
                "point_handle_objects": [Writer.next_index - 2, Writer.next_index - 1],
                "point_native_ids": [PointIds[Index] for Index in Operands],
            }
        )
    Geometry: SketchGeometry = {
        "object_index": Current,
        "body_start": 0,
        "geometry_end": 0,
        "next_map_index": Writer.next_index,
        "points_metres": [
            (0.004, 0.007),
            (0.027, 0.030),
            (0.004, 0.030),
            (0.027, 0.007),
            (0.0, 0.0),
        ],
        "point_relation_tallies": [{"id": Point, "tally": 0} for Point in PointIds],
        "external_point_references": [
            {
                "local_id": PointIds[4],
                "feature_id": 8,
                "feature_time": 123,
                "handle_class": KPointHandle,
                "handle_fields": (0, -1, 0),
            }
        ],
        "lines": [],
        "length_dimensions": Rows,
        "member_relations": [],
    }
    for Name in (KLineHandle, KLineHandle, KObjectList):
        Writer.BeginObject(Name, 1)
    return Writer.Snapshot(), Geometry, Earlier


# the false callers contradict the earlier owner and the actual display ordinal
def CheckWrongOwner(
    Initial: PartArchiveState,
    Geometry: SketchGeometry,
    Earlier: int,
    DataValue: bytes,
    FinalState: PartArchiveState,
) -> int:
    EarlierGeometry = CopyValue(Geometry)
    EarlierGeometry["object_index"] = Earlier
    Swapped = CopyValue(Geometry)
    Rows = Swapped["length_dimensions"]
    Rows[0], Rows[1] = Rows[1], Rows[0]
    ReversedRole = CopyValue(Geometry)
    Dims = ReversedRole["length_dimensions"]
    Dims[0]["point_native_ids"], Dims[1]["point_native_ids"] = (
        Dims[1]["point_native_ids"],
        Dims[0]["point_native_ids"],
    )
    Later = PartArchiveWriter(Initial)
    Later.BeginObject(KSketchClass, 1)
    Refusals = (
        (Initial, EarlierGeometry, 0, 81),
        (Later.Snapshot(), Geometry, 0, 81),
        (Initial, Geometry, 1, 84),
        (Initial, Geometry, 0, 84),
        (Initial, Swapped, 0, 84),
        (Initial, ReversedRole, 0, 81),
    )
    for StateValue, Shape, SlotValue, Identity in Refusals:
        try:
            EncodePadDimLink(KConfigGen, StateValue, Shape, SlotValue, Identity)
        except ArchiveError:
            continue
        raise ValueError("Constructor accepted a contradictory dimension owner or role")
    for Corrupt in (
        DataValue[:-6] + EncodeObjectRef(Earlier) + PackFields("<i", 0),
        DataValue[:-4] + PackFields("<i", 1),
    ):
        try:
            VerifyOwner(Corrupt, Initial, FinalState, Geometry["object_index"], 0)
        except ArchiveError:
            continue
        raise ValueError("Reader accepted a contradictory owning sketch or order")
    return len(Refusals) + 2


# freshly allocated shifted dimensions and display slots all preserve their own order
def CheckDimTrial() -> dict[str, object]:
    StateValue, Geometry, Earlier = BuildDimTrial()
    Records: list[dict[str, object]] = []
    Negative = 0
    for SlotValue, DimValue in enumerate(Geometry["length_dimensions"]):
        Display = PartArchiveWriter(StateValue)
        Display.BeginObject(KDisplayClass, 1)
        Initial = Display.Snapshot()
        Identity = DimValue["native_id"]
        DataValue, FinalState = EncodePadDimLink(
            KConfigGen, Initial, Geometry, SlotValue, Identity
        )
        VerifyOwner(DataValue, Initial, FinalState, Geometry["object_index"], SlotValue)
        if SlotValue == 0:
            Negative = CheckWrongOwner(
                Initial, Geometry, Earlier, DataValue, FinalState
            )
        Favorites = PartArchiveWriter(FinalState)
        Favorites.BeginObject(KFavoriteClass, 1)
        StateValue = Favorites.Snapshot()
        Records.append(
            {
                "slot": SlotValue,
                "dimension_id": Identity,
                "record_bytes": len(DataValue),
                "record_sha256": ShaValue(DataValue).hexdigest(),
                "allocations": [Initial.NextIndex, FinalState.NextIndex],
            }
        )
    return {
        "sketch_slot": Geometry["object_index"],
        "owners": Records,
        "negative_controls": Negative,
    }


# the report seals only scoped results and leaves all native sources private
def ReportPadLinks(Directory: FilePath) -> dict[str, object]:
    Directory = Directory.resolve(strict=True)
    Native = AuditDiscovery(Directory, KRepository, *KCapturePins, True)
    Evidence = ReadJsonPin(Directory / "report.json", KCapturePins[1])
    return {
        "application_build": Native["application_build"],
        "native_report_sha256": KCapturePins[1],
        "healthy_stock_controls": Native["stock_controls"],
        "native_observations": Native["verified_native_observations"],
        "licensed_archives": {
            Case["variant"]: ReplayDimLink(Directory, Case)
            for Case in Evidence["observations"]["cases"]
        },
        "fresh_control": CheckDimTrial(),
    }


# the command retains the private source directory without changing it
def RunPadDimLinks() -> None:
    Parser = ArgumentParser(description=__doc__)
    Parser.add_argument("--run-directory", required=True, type=FilePath)
    print(DumpJson(ReportPadLinks(Parser.parse_args().run_directory), sort_keys=True))


if __name__ == "__main__":
    RunPadDimLinks()
