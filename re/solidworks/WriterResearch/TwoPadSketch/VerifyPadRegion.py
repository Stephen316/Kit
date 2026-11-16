# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Verify the upper-pad sketch region against exact retained discovery inputs."""

from argparse import ArgumentParser
from copy import deepcopy as CopyValue
from hashlib import sha256 as ShaValue
from json import dumps as DumpJson
from pathlib import Path as FilePath
import sys

# the replay uses the checked out types and separate sealed discovery verifier
KRepository = FilePath(__file__).resolve().parents[4]

# declare the source paths needed by the existing standalone research helpers
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

from OriginSketch import KObjectList, KSketchClass
from PadReceipts import ReadPadBytes
from PartArchive import PartArchiveState, PartArchiveWriter
from PilotEvidence import pinned_record as ReadJsonPin
from RectangleCorners import KLineHandle
from RectangleRegion import KRegionClass
from VerifyDiscovery import AuditDiscovery
from VerifyPadCap import KCapturePins
from VerifyPadEqual import OpenPadLines, ReadPadLane, SavePadState
from WritePadEqual import EncodePadEqual
from WritePadRegion import EncodePadRegion
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import ArchiveError, KClassRefKind
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Resolved.Cut.CutProfileBody import ReadCutBody
from convert.adapters.solidworks.Sketch.Cursor import SketchArchive
from convert.adapters.solidworks.Sketch.Displays import ReadDisplays
from convert.adapters.solidworks.Sketch.GeometryTypes import (
    SketchGeometry,
    SketchLine,
    SketchRelation,
)
from convert.adapters.solidworks.Sketch.Regions import (
    ReadOutline,
    ReadRegion,
    ReadRegionStart,
)


# inspect the exact emitter order instead of sorting away contour semantics
def ReadPadOutline(Cursor: SketchArchive) -> tuple[int, ...]:
    Cursor.TakePointer((KObjectList,), KClassRefKind, CompactOnly=True)
    RequireArch(Cursor.ReadInts("<H"), (1,), "one upper-pad region")
    Cursor.TakePointer((KRegionClass,), KClassRefKind, CompactOnly=True)
    Cursor.TakePointer((KObjectList,), KClassRefKind, CompactOnly=True)
    RequireArch(Cursor.ReadInts("<H"), (4,), "four upper-pad outline handles")
    return tuple(ReadOutline(Cursor, 4))


# the existing sketch decoder owns the region and exact empty managers at return
def ReadRegionEnd(Cursor: SketchArchive, Geometry: SketchGeometry) -> None:
    ReadRegion(Cursor, Geometry["lines"])
    RequireArch(Cursor.ReadInts("<H7i"), (0,) * 8, "complete empty post-region return")


# compare fresh order and complete readback before claiming a successful round trip
def VerifyRegion(
    DataValue: bytes,
    Initial: PartArchiveState,
    FinalState: PartArchiveState,
    Geometry: SketchGeometry,
    Outline: tuple[int, ...],
) -> None:
    Ordered = SketchArchive(Initial.Cursor(DataValue, 0))
    RequireArch(ReadPadOutline(Ordered), Outline, "same emitted contour order")
    Cursor = SketchArchive(Initial.Cursor(DataValue, 0))
    ReadRegionEnd(Cursor, Geometry)
    RequireArch(Cursor.Offset, len(DataValue), "exact inline sketch return")
    RequireArch(SavePadState(Cursor), FinalState, "same complete region allocations")


# the continuously read outer profile has a different chain after this sketch ends
def ReplayRegion(Directory: FilePath, Capture: dict) -> dict[str, object]:
    SaveValue = Capture["save"]
    Archive = SldprtArchive.from_bytes(
        ReadPadBytes(Directory, SaveValue["file"], SaveValue["sha256"])
    )
    Resolved = Archive.require("Contents/Config-0-ResolvedFeatures")
    Cursor, Geometry, _ = OpenPadLines(Archive.require("Contents/Config-0"), Resolved)
    ReadPadLane(Cursor, Geometry)
    ReadDisplays(Cursor, Geometry)
    ReadRegionStart(Cursor)
    Start = Cursor.Offset
    Initial = SavePadState(Cursor)
    Ordered = SketchArchive(Initial.Cursor(Resolved, Start))
    Outline = ReadPadOutline(Ordered)
    ReadRegionEnd(Cursor, Geometry)
    StopValue = Cursor.Offset
    Observed = SavePadState(Cursor)
    BodyValue = ReadCutBody(Cursor, Geometry["object_index"])
    OuterChain = BodyValue["chain"]["edge_ids"]
    RequireArch(
        set(Outline).isdisjoint(OuterChain), True, "different outer projected chain"
    )
    DataValue, FinalState = EncodePadRegion(KConfigGen, Initial, Geometry, Outline)
    VerifyRegion(DataValue, Initial, FinalState, Geometry, Outline)
    RequireArch(
        DataValue == Resolved[Start:StopValue], True, "exact saved region and return"
    )
    RequireArch(FinalState, Observed, "same complete saved region allocations")
    return {
        "archive_sha256": SaveValue["sha256"],
        "record_bytes": len(DataValue),
        "record_sha256": ShaValue(DataValue).hexdigest(),
        "outline": Outline,
        "outer_projected_chain": OuterChain,
        "allocations": [Initial.NextIndex, FinalState.NextIndex],
    }


# an earlier sketch gives fresh allocations a distinct region and foreign handle
def BuildRegionTrial() -> tuple[PartArchiveState, SketchGeometry, int, int]:
    Writer = PartArchiveWriter()
    Writer.BeginObject(KSketchClass, 1)
    EarlierSketch = Writer.next_index - 1
    Writer.BeginObject(KObjectList, 1)
    Writer.BeginObject(KRegionClass, 1)
    Writer.BeginObject(KLineHandle, 1)
    EarlierHandle = Writer.next_index - 1
    Writer.BeginObject(KSketchClass, 1)
    SketchIndex = Writer.next_index - 1
    Lines: list[SketchLine] = []
    Axes: list[SketchRelation] = []
    for Ordinal, (LineId, Endpoints, Code, Kind) in enumerate(
        (
            (22, [0, 3], 5, "vertical"),
            (21, [0, 1], 4, "horizontal"),
            (31, [1, 2], 5, "vertical"),
            (42, [3, 2], 4, "horizontal"),
        ),
        start=1,
    ):
        Handle = Writer.next_index
        Writer.BeginObject(KLineHandle, 1)
        Lines.append(
            {
                "member_index": Ordinal,
                "native_id": LineId,
                "flags": 4,
                "point_indices": Endpoints,
            }
        )
        Axes.append(
            {
                "start": 0,
                "end": 0,
                "line_handle_object": Handle,
                "line_handle_fields": (LineId, -1, 0),
                "segment_native_id": LineId,
                "type_code": Code,
                "kind": Kind,
                "scalar_fields": (65534, 0),
            }
        )
    Geometry: SketchGeometry = {
        "object_index": SketchIndex,
        "body_start": 0,
        "geometry_end": 0,
        "next_map_index": Writer.next_index,
        "points_metres": [
            (0.002, 0.004),
            (0.025, 0.004),
            (0.025, 0.027),
            (0.002, 0.027),
        ],
        "point_relation_tallies": [],
        "external_point_references": [],
        "lines": Lines,
        "length_dimensions": [],
        "member_relations": Axes,
    }
    _, Initial = EncodePadEqual(KConfigGen, Writer.Snapshot(), Geometry, (22, 21))
    return Initial, Geometry, EarlierSketch, EarlierHandle


# both allocation joins and contour membership must fail before returning bytes
def CheckRegionTrial() -> dict[str, object]:
    Initial, Geometry, EarlierSketch, EarlierHandle = BuildRegionTrial()
    Outline = (31, 42, 22, 21)
    DataValue, FinalState = EncodePadRegion(KConfigGen, Initial, Geometry, Outline)
    VerifyRegion(DataValue, Initial, FinalState, Geometry, Outline)
    WrongSketch = CopyValue(Geometry)
    WrongSketch["object_index"] = EarlierSketch
    WrongHandle = CopyValue(Geometry)
    WrongHandle["member_relations"][0]["line_handle_object"] = EarlierHandle
    LaterSketch = PartArchiveWriter(Initial)
    LaterSketch.BeginObject(KSketchClass, 1)
    Refusals = (
        (Initial, Geometry, (31, 42, 31, 21)),
        (Initial, Geometry, (31, 42, 22, 24)),
        (Initial, Geometry, (31, 22, 42, 21)),
        (Initial, WrongSketch, Outline),
        (Initial, WrongHandle, Outline),
        (LaterSketch.Snapshot(), Geometry, Outline),
        (FinalState, Geometry, Outline),
    )
    for StateValue, GeometryValue, Edges in Refusals:
        try:
            EncodePadRegion(KConfigGen, StateValue, GeometryValue, Edges)
        except ArchiveError:
            continue
        raise ValueError("Constructor accepted a contradictory sketch or contour")
    for Corrupt in (DataValue[:-1] + bytes([1]), DataValue + bytes(1)):
        try:
            VerifyRegion(Corrupt, Initial, FinalState, Geometry, Outline)
        except ArchiveError:
            continue
        raise ValueError("Reader accepted a contradictory sketch return")
    return {
        "record_bytes": len(DataValue),
        "record_sha256": ShaValue(DataValue).hexdigest(),
        "outline": Outline,
        "allocations": [Initial.NextIndex, FinalState.NextIndex],
        "negative_controls": len(Refusals) + 2,
    }


# the deterministic digest report leaves all licensed source assets sealed
def ReportPadRegion(Directory: FilePath) -> dict[str, object]:
    Directory = Directory.resolve(strict=True)
    Native = AuditDiscovery(Directory, KRepository, *KCapturePins, True)
    ReportValue = ReadJsonPin(Directory / "report.json", KCapturePins[1])
    return {
        "application_build": Native["application_build"],
        "native_report_sha256": KCapturePins[1],
        "healthy_stock_controls": Native["stock_controls"],
        "native_observations": Native["verified_native_observations"],
        "licensed_archives": {
            Capture["variant"]: ReplayRegion(Directory, Capture)
            for Capture in ReportValue["observations"]["cases"]
        },
        "fresh_control": CheckRegionTrial(),
    }


# the command accepts the existing evidence directory without writing into it
def RunPadRegion() -> None:
    Parser = ArgumentParser(description=__doc__)
    Parser.add_argument("--run-directory", required=True, type=FilePath)
    print(DumpJson(ReportPadRegion(Parser.parse_args().run_directory), sort_keys=True))


if __name__ == "__main__":
    RunPadRegion()
