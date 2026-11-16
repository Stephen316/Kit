# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Replay the upper-pad logical relation against receipt-pinned licensed saves."""

from argparse import ArgumentParser
from copy import deepcopy as CopyValue
from hashlib import sha256 as ShaValue
from json import dumps as DumpJson
from pathlib import Path as FilePath
import sys

# the offline runner resolves the existing private custody and archive readers
KRepository = FilePath(__file__).resolve().parents[4]

# the runner shares existing research helpers without installing private code
sys.path[:0] = [
    str(KRepository / Lane)
    for Lane in (
        "src",
        "re/automation",
        "re/automation/TwoPad",
        "re/solidworks/WriterResearch",
    )
]

from PadGeometry import KSavedPhases
from PadReceipts import ReadPadBytes
from PartArchive import PartArchiveState, PartArchiveWriter
from PilotEvidence import pinned_record as ReadJsonPin
from VerifyDiscovery import AuditDiscovery
from WritePadEqual import EncodePadEqual, KPadEqualCode
from convert.adapters.solidworks.Config.OrdinaryMap import ReadEmptyMap
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import (
    ArchiveError,
    KClassRefKind,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Resolved.ProfileEntry import ReadProfileHead
from convert.adapters.solidworks.Resolved.ResolvedHead import OpenResolved
from convert.adapters.solidworks.Resolved.TwoPad.PadHistory import (
    KPadListCount,
    ReadBasePad,
)
from convert.adapters.solidworks.Resolved.TwoPad.PadProfile import (
    PadLinePair,
    ReadPadPair,
)
from convert.adapters.solidworks.Sketch.Cursor import SketchArchive
from convert.adapters.solidworks.Sketch.Geometry import ReadGeoSpansMut
from convert.adapters.solidworks.Sketch.GeometryTypes import (
    SketchGeometry,
    SketchLine,
    SketchRelation,
)
from convert.adapters.solidworks.Sketch.SketchTail import (
    ReadLogicalEnd,
    ReadRelationEnd,
    ReadSketchEnd,
)

# the same pinned discovery receipt binds both healthy phases
KCaptureSource = "463a3de14e4cb34aeeaa6aed1aa1e8b2804572c8"

# this receipt joins distinct saved inputs to their licensed observation phases
KReportSha = "bf0d74c06878c6c5063e4b9a55c61c2ef258bdc24323adbfb8f8d069bc77697e"

# the authoring phase owns all five saved native archives
KAuthorSha = "7c25ed3111ec45d9646e7b5de9df16f90f57528d3f2b97fc4e14f2666a2a884f"

# the independent reopen phase measures each archived owner across rebuild
KReopenSha = "1ebdcdc23d4d220d549573dfb2c0cb45b1697ec7e42c192a3fb95bd34ba5699b"


# a complete snapshot verifies compact reader allocation ownership
def SavePadState(Cursor: ArchiveCursor) -> PartArchiveState:
    return PartArchiveState(
        Cursor.NextIndex,
        tuple(sorted(Cursor.Classes.items())),
        tuple(sorted(Cursor.Objects.items())),
    )


# typed config and base transitions locate the upper profile before reading its lines
def OpenPadLines(
    ConfigData: bytes, Resolved: bytes
) -> tuple[SketchArchive, SketchGeometry, str]:
    Mapping, _ = ReadEmptyMap(ConfigData, (2,))
    Parent = OpenResolved(Resolved, Mapping, KPadListCount)
    ReadBasePad(Parent)
    Parent.TakePointer(("moProfileFeature_c",), KClassRefKind, CompactOnly=True)
    Parent.TakePointer(("moNodeName_c",), KClassRefKind, CompactOnly=True)
    OwnerName, _, _ = ReadProfileHead(Parent, (0x40000000, 0xC0000000))
    _, _, SketchIndex = Parent.TakePointer(
        ("sgSketch",), KClassRefKind, CompactOnly=True
    )
    Cursor = SketchArchive(Parent)
    Geometry, _ = ReadGeoSpansMut(Cursor, SketchIndex)
    return Cursor, Geometry, OwnerName


# the three licensed snapshots supply independent source targets
def ReadApiPair(Capture: dict, OwnerName: str) -> tuple[int, int]:
    Phases: list[tuple[int, int]] = []
    for PhaseName in KSavedPhases:
        (SketchValue,) = (
            Row for Row in Capture[PhaseName]["sketches"] if Row["name"] == OwnerName
        )
        (Relation,) = (
            Row for Row in SketchValue["relations"] if Row["type"] == KPadEqualCode
        )
        RequireArch(
            Relation["entity_types"], [3, 3], "licensed sketch segment operands"
        )
        First, Second = Relation["entities"]
        for Operand in (First, Second):
            FirstId, SecondId = Operand["id"]
            RequireArch(
                Operand["segment_type"] == 0 and FirstId == SecondId,
                True,
                "licensed native line identity",
            )
        Phases.append((First["id"][0], Second["id"][0]))
    RequireArch(len(set(Phases)), 1, "stable licensed directed operand order")
    return Phases[0]


# the existing reader consumes both logical returns and exposes the next owner boundary
def ReadPadLane(Cursor: SketchArchive, Geometry: SketchGeometry) -> PadLinePair:
    PairValue = ReadPadPair(Cursor, Geometry)
    ReadRelationEnd(Cursor)
    ReadLogicalEnd(Cursor)
    return PairValue


# every newly constructed compact record must read through both logical returns
def CheckNewLane(
    Initial: PartArchiveState,
    FinalState: PartArchiveState,
    Geometry: SketchGeometry,
    DataValue: bytes,
    LineIds: tuple[int, int],
) -> PadLinePair:
    Cursor = SketchArchive(Initial.Cursor(DataValue, 0))
    PairValue = ReadPadLane(Cursor, Geometry)
    RequireArch(
        (PairValue.CodeValue, PairValue.Lines, PairValue.Handles),
        (KPadEqualCode, LineIds, (Initial.NextIndex, Initial.NextIndex + 1)),
        "fresh ordered typed line allocations",
    )
    RequireArch(Cursor.Offset, len(DataValue), "exact fresh logical return")
    RequireArch(SavePadState(Cursor), FinalState, "exact fresh object ownership")
    return PairValue


# compare generated fields to a sealed source only after measuring its typed owner
def CheckPadSave(Directory: FilePath, Capture: dict) -> dict[str, object]:
    SaveValue = Capture["save"]
    Archive = SldprtArchive.from_bytes(
        ReadPadBytes(Directory, SaveValue["file"], SaveValue["sha256"])
    )
    Resolved = Archive.require("Contents/Config-0-ResolvedFeatures")
    Cursor, Geometry, OwnerName = OpenPadLines(
        Archive.require("Contents/Config-0"), Resolved
    )
    Start = Cursor.Offset
    Initial = SavePadState(Cursor)
    LineIds = ReadApiPair(Capture, OwnerName)
    Observed = ReadPadLane(Cursor, Geometry)
    StopValue = Cursor.Offset
    OwnerState = SavePadState(Cursor)
    ReadSketchEnd(Cursor, Geometry)
    RequireArch(Observed.Lines, LineIds, "same API and archived line ownership")
    DataValue, FinalState = EncodePadEqual(KConfigGen, Initial, Geometry, LineIds)
    RequireArch(
        DataValue == Resolved[Start:StopValue],
        True,
        "fresh fields match the entire saved logical lane",
    )
    RequireArch(FinalState, OwnerState, "same saved next archive state")
    Readback = CheckNewLane(Initial, FinalState, Geometry, DataValue, LineIds)
    RequireArch(Readback.Handles, Observed.Handles, "same saved allocated handles")
    return {
        "archive_sha256": SaveValue["sha256"],
        "record_bytes": len(DataValue),
        "record_sha256": ShaValue(DataValue).hexdigest(),
        "member_ids": LineIds,
        "allocated_handles": Readback.Handles,
    }


# different local identities and an earlier sketch challenge active ownership
def BuildPadTrial() -> tuple[PartArchiveState, SketchGeometry]:
    Writer = PartArchiveWriter()
    Writer.BeginObject("sgSketch", 1)
    Writer.BeginObject("sgLineHandle", 1)
    Writer.BeginObject("sgSketch", 1)
    SketchIndex = Writer.next_index - 1
    Lines: list[SketchLine] = [
        {"member_index": 0, "native_id": -1, "flags": 5, "point_indices": [0, 2]}
    ]
    Axes: list[SketchRelation] = []
    for Ordinal, (LineId, Indices, AxisCode, AxisName) in enumerate(
        (
            (22, [0, 3], 5, "vertical"),
            (21, [0, 1], 4, "horizontal"),
            (31, [1, 2], 5, "vertical"),
            (42, [3, 2], 4, "horizontal"),
        ),
        start=1,
    ):
        Handle = Writer.next_index
        Writer.BeginObject("sgLineHandle", 1)
        Lines.append(
            {
                "member_index": Ordinal,
                "native_id": LineId,
                "flags": 4,
                "point_indices": Indices,
            }
        )
        Axes.append(
            {
                "start": 0,
                "end": 0,
                "line_handle_object": Handle,
                "line_handle_fields": (LineId, -1, 0),
                "segment_native_id": LineId,
                "type_code": AxisCode,
                "kind": AxisName,
                "scalar_fields": (65534, 0),
            }
        )
    StateValue = Writer.Snapshot()
    return StateValue, {
        "object_index": SketchIndex,
        "body_start": 0,
        "geometry_end": 0,
        "next_map_index": StateValue.NextIndex,
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


# each contradictory caller input must fail before a packet can be returned
def CheckBadLane(
    Generation: int,
    StateValue: PartArchiveState,
    Geometry: SketchGeometry,
    LineIds: tuple[int, int],
    Label: str,
) -> None:
    try:
        EncodePadEqual(Generation, StateValue, Geometry, LineIds)
    except ArchiveError:
        return
    raise ValueError(f"Constructor accepted {Label}")


# fresh ownership and geometry controls do not depend on any measured source values
def CheckTrial(
    StateValue: PartArchiveState, Geometry: SketchGeometry
) -> dict[str, object]:
    LineIds = (22, 21)
    DataValue, FinalState = EncodePadEqual(KConfigGen, StateValue, Geometry, LineIds)
    PairValue = CheckNewLane(StateValue, FinalState, Geometry, DataValue, LineIds)
    BadTargets = (
        ((22, 22), "duplicate operands"),
        ((21, 22), "reversed operand order"),
        ((22, 31), "parallel operands"),
        ((22, -1), "helper member"),
        ((22, 65535), "foreign member"),
    )
    for Targets, Label in BadTargets:
        CheckBadLane(KConfigGen, StateValue, Geometry, Targets, Label)

    Unequal = CopyValue(Geometry)
    Unequal["points_metres"][1] = (0.026, 0.004)
    Unequal["points_metres"][2] = (0.026, 0.027)
    Forged = CopyValue(Geometry)
    Forged["member_relations"][0]["line_handle_fields"] = (22, 12, 0)
    Earlier = CopyValue(Geometry)
    Earlier["member_relations"][0]["line_handle_object"] = next(
        Index
        for Index, Name in StateValue.Objects
        if Name == "sgLineHandle" and Index < Geometry["object_index"]
    )
    Stale = CopyValue(Geometry)
    Stale["object_index"] = next(
        Index for Index, Name in StateValue.Objects if Name == "sgSketch"
    )
    Duplicate = CopyValue(Geometry)
    Duplicate["lines"][4]["point_indices"] = [0, 1]
    BadGeometry = (
        (Unequal, "unequal rectangular operands"),
        (Forged, "forged external ownership"),
        (Earlier, "handle owned by the earlier sketch"),
        (Stale, "stale sketch owner"),
        (Duplicate, "duplicate perimeter side"),
    )
    for Altered, Label in BadGeometry:
        CheckBadLane(KConfigGen, StateValue, Altered, LineIds, Label)
    CheckBadLane(KConfigGen - 1, StateValue, Geometry, LineIds, "other generation")

    AlteredReturn = DataValue[:-1] + bytes([DataValue[-1] ^ 1])
    try:
        ReadPadLane(SketchArchive(StateValue.Cursor(AlteredReturn, 0)), Geometry)
    except ArchiveError:
        return {
            "record_sha256": ShaValue(DataValue).hexdigest(),
            "record_bytes": len(DataValue),
            "member_ids": LineIds,
            "allocated_handles": PairValue.Handles,
            "negative_controls": len(BadTargets) + len(BadGeometry) + 2,
        }
    raise ValueError("Reader accepted the altered logical return")


# the report records scoped archive readback without persisting any native bytes
def ReportPadEqual(Directory: FilePath) -> dict[str, object]:
    Directory = Directory.resolve(strict=True)
    Native = AuditDiscovery(
        Directory, KRepository, KCaptureSource, KReportSha, KAuthorSha, KReopenSha, True
    )
    ReportValue = ReadJsonPin(Directory / "report.json", KReportSha)
    Cases = {
        Capture["variant"]: CheckPadSave(Directory, Capture)
        for Capture in ReportValue["observations"]["cases"]
    }
    StateValue, Geometry = BuildPadTrial()
    return {
        "application_build": Native["application_build"],
        "native_report_sha256": KReportSha,
        "native_capture_source_revision": KCaptureSource,
        "verified_native_observations": Native["verified_native_observations"],
        "healthy_stock_controls": Native["stock_controls"],
        "licensed_archive_replays": Cases,
        "fresh_control": CheckTrial(StateValue, Geometry),
    }


# a dedicated entry point accepts a private path without writing native artifacts
def RunPadEqual() -> None:
    Parser = ArgumentParser(description=__doc__)
    Parser.add_argument("--run-directory", required=True, type=FilePath)
    print(DumpJson(ReportPadEqual(Parser.parse_args().run_directory), sort_keys=True))


if __name__ == "__main__":
    RunPadEqual()
