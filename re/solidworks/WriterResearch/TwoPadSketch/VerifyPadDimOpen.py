# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Replay only the saved upper-pad display openings and their owner boundaries."""

from argparse import ArgumentParser
from dataclasses import replace as Replace
from hashlib import sha256 as ShaValue
from json import dumps as DumpJson
from pathlib import Path as FilePath
from struct import calcsize as CalcSize, pack as PackFields
import sys

# the pinned inline research readers stay in the exact source checkout
KRepository = FilePath(__file__).resolve().parents[4]

# explicit research roots allow direct replay without package runtime dependencies
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
from DisplayStyle import KInlineTextTailFormat, KTextPositionFormat
from OriginSketch import KObjectList
from PadGeometry import CheckVector, KSavedPhases
from PadReceipts import ReadPadBytes
from PartArchive import PartArchiveState, PartArchiveWriter
from PilotEvidence import pinned_record as ReadJsonPin
from RectDimDisplay import KSketchHandle
from DisplayFavorite import KFavoriteClass
from VerifyDiscovery import AuditDiscovery
from VerifyPadCap import KCapturePins
from VerifyPadDimLink import BuildDimTrial, CheckNativeDims
from VerifyPadEqual import OpenPadLines, ReadPadLane, SavePadState
from WritePadDimLink import EncodePadDimLink
from WritePadDimOpen import EncodePadDimOpen, PadDimView
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import ArchiveError, EncodeObjectRef
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Resolved.Support.FaceFrame import FaceFrame
from convert.adapters.solidworks.Resolved.TwoPad.PadHistory import ReadPadHistory
from convert.adapters.solidworks.Sketch.Cursor import SketchArchive
from convert.adapters.solidworks.Sketch.DimHandle import ReadDimHandle
from convert.adapters.solidworks.Sketch.DisplayOpen import ReadDisplayOpen
from convert.adapters.solidworks.Sketch.GeometryTypes import SketchGeometry
from convert.adapters.solidworks.Sketch.Displays import ReadSavedDimEnd, TakeShownClass
from convert.adapters.solidworks.Sketch.Regions import ReadRegionStart

# the pinned api calls provide independent nominal annotation ordinates
KAuthoredText = ((0.075, 0.075), (0.075, 0.075), (0.072, 0.073), (0.071, 0.073))

# the established inline text framing locates the world anchor after a typed read
KAnchorTailSize = (
    CalcSize(KTextPositionFormat) + CalcSize("<Hi") + CalcSize(KInlineTextTailFormat)
)


# the display reader proves its exact opening before recovering the typed anchor
def ReadPadView(
    Cursor: SketchArchive,
    SketchIndex: int,
    PlaneOrigin: tuple[float, float, float],
    PlaneNormal: tuple[float, float, float],
) -> PadDimView:
    Header = FieldCursor(Cursor.BlobValue, Cursor.Offset)
    RequireArch(Header.ReadInts("<4H"), (0,) * 4, "guarded opening and three nulls")
    VisualIndex = Header.ReadValue("<2i2HBIHhf2Hi")[-1]
    ReadDisplayOpen(Cursor, True)
    Fields = FieldCursor(Cursor.BlobValue, Cursor.Offset - KAnchorTailSize)
    CoordX, CoordY, CoordZ = Fields.ReadPoint(3)
    return PadDimView(
        SketchIndex, VisualIndex, PlaneOrigin, PlaneNormal, (CoordX, CoordY, CoordZ)
    )


# the independently measured native support joins the selected archive plane
def CheckViewFrame(Capture: dict, Frame: FaceFrame) -> None:
    OriginMetres = Frame["root_metres"]
    NormalWorld = Frame["normal_world"]
    for PhaseName in KSavedPhases:
        Support = Capture[PhaseName]["upper_support"]
        CheckVector(
            Support["origin_world_mm"],
            tuple(Value * 1000 for Value in OriginMetres),
            "independent display support origin",
        )
        CheckVector(Support["normal_world"], NormalWorld, "display support normal")


# the composed read ends at the same separate sketch alias and ordinal
def VerifyOpenLink(
    Opening: bytes,
    LinkValue: bytes,
    Initial: PartArchiveState,
    FinalState: PartArchiveState,
    ViewValue: PadDimView,
    SlotValue: int,
) -> None:
    Cursor = SketchArchive(Initial.Cursor(Opening + LinkValue, 0))
    RequireArch(
        ReadPadView(
            Cursor, ViewValue.SketchIndex, ViewValue.PlaneOrigin, ViewValue.PlaneNormal
        ),
        ViewValue,
        "fresh visual slot and world anchor",
    )
    RequireArch(Cursor.Offset, len(Opening), "separate opening boundary")
    RequireArch(SavePadState(Cursor), Initial, "opening has no allocations")
    TakeShownClass(Cursor, KSketchHandle)
    RequireArch(
        ReadDimHandle(Cursor, ViewValue.SketchIndex),
        SlotValue,
        "same following owner slot",
    )
    RequireArch(Cursor.Offset, len(Opening) + len(LinkValue), "complete following link")
    RequireArch(
        SavePadState(Cursor), FinalState, "same complete linked allocation state"
    )


# exact saved intervals establish the opening bytes without reusing any saved block
def ReplayDimOpen(Directory: FilePath, Capture: dict) -> dict[str, object]:
    SaveValue = Capture["save"]
    Archive = SldprtArchive.from_bytes(
        ReadPadBytes(Directory, SaveValue["file"], SaveValue["sha256"])
    )
    ConfigData = Archive.require("Contents/Config-0")
    Resolved = Archive.require("Contents/Config-0-ResolvedFeatures")
    History = ReadPadHistory(ConfigData, Resolved)
    Frame = History.Support["face"]["plane"]
    CheckViewFrame(Capture, Frame)
    RootX, RootY, RootZ = Frame["root_metres"]
    NormX, NormY, NormZ = Frame["normal_world"]
    Cursor, Geometry, OwnerName = OpenPadLines(ConfigData, Resolved)
    CheckNativeDims(Capture, Geometry, OwnerName)
    ReadPadLane(Cursor, Geometry)
    TakeShownClass(Cursor, KObjectList)
    RequireArch(Cursor.ReadInts("<H"), (4,), "four saved upper display openings")
    Records: list[dict[str, object]] = []
    for SlotValue, DimValue in enumerate(Geometry["length_dimensions"]):
        TakeShownClass(Cursor, KDisplayClass)
        Start = Cursor.Offset
        Initial = SavePadState(Cursor)
        ViewValue = ReadPadView(
            Cursor,
            Geometry["object_index"],
            (RootX, RootY, RootZ),
            (NormX, NormY, NormZ),
        )
        CheckVector(
            list(ViewValue.TextWorld[:2]),
            KAuthoredText[SlotValue],
            "authored display text ordinate",
        )
        EndOffset = Cursor.Offset
        RequireArch(SavePadState(Cursor), Initial, "saved opening adds no allocations")
        TakeShownClass(Cursor, KSketchHandle)
        RequireArch(
            ReadDimHandle(Cursor, ViewValue.SketchIndex),
            SlotValue,
            "saved adjacent owner slot",
        )
        Identity = DimValue["native_id"]
        Opening = EncodePadDimOpen(
            KConfigGen, Initial, Geometry, SlotValue, Identity, ViewValue
        )
        LinkValue, FinalState = EncodePadDimLink(
            KConfigGen, Initial, Geometry, SlotValue, Identity
        )
        RequireArch(
            Opening == Resolved[Start:EndOffset], True, "byte exact saved opening"
        )
        RequireArch(
            LinkValue == Resolved[EndOffset : Cursor.Offset],
            True,
            "same adjacent owner",
        )
        RequireArch(
            SavePadState(Cursor), FinalState, "same saved linked allocation map"
        )
        VerifyOpenLink(Opening, LinkValue, Initial, FinalState, ViewValue, SlotValue)
        ReadSavedDimEnd(Cursor, DimValue["metres"])
        Records.append(
            {
                "slot": SlotValue,
                "dimension_id": Identity,
                "visual_index": ViewValue.VisualIndex,
                "opening_bytes": len(Opening),
                "opening_sha256": ShaValue(Opening).hexdigest(),
                "linked_owner_sha256": ShaValue(LinkValue).hexdigest(),
                "text_world": ViewValue.TextWorld,
            }
        )
    ReadRegionStart(Cursor)
    return {
        "archive_sha256": SaveValue["sha256"],
        "support_height_m": RootZ,
        "openings": Records,
    }


# foreign source values and mismatched slot or frame cases must refuse independently
def CheckOpenTrial() -> dict[str, object]:
    StateValue, Geometry, Earlier = BuildDimTrial()
    Records: list[dict[str, object]] = []
    Controls = 0
    for SlotValue, DimValue in enumerate(Geometry["length_dimensions"]):
        Display = PartArchiveWriter(StateValue)
        Display.BeginObject(KDisplayClass, 1)
        Initial = Display.Snapshot()
        ViewValue = PadDimView(
            Geometry["object_index"],
            SlotValue + 12,
            (0.0, 0.0, 0.021),
            (0.0, 0.0, 1.0),
            (
                0.043 + SlotValue * 0.003,
                0.051 + SlotValue * 0.002,
                0.0211 if SlotValue == 3 else 0.021,
            ),
        )
        Identity = DimValue["native_id"]
        Opening = EncodePadDimOpen(
            KConfigGen, Initial, Geometry, SlotValue, Identity, ViewValue
        )
        LinkValue, FinalState = EncodePadDimLink(
            KConfigGen, Initial, Geometry, SlotValue, Identity
        )
        VerifyOpenLink(Opening, LinkValue, Initial, FinalState, ViewValue, SlotValue)
        Controls += RefuseOpenData(
            Initial,
            Geometry,
            SlotValue,
            Identity,
            ViewValue,
            Earlier,
            Opening,
            LinkValue,
            FinalState,
        )
        Favorites = PartArchiveWriter(FinalState)
        Favorites.BeginObject(KFavoriteClass, 1)
        StateValue = Favorites.Snapshot()
        Records.append(
            {
                "slot": SlotValue,
                "visual_index": ViewValue.VisualIndex,
                "dimension_id": Identity,
                "opening_bytes": len(Opening),
                "opening_sha256": ShaValue(Opening).hexdigest(),
                "text_world": ViewValue.TextWorld,
            }
        )
    return {
        "fresh_sketch_slot": Geometry["object_index"],
        "openings": Records,
        "negative_controls": Controls,
    }


# a typed earlier alias and a different ordinal also exercise the real reader
def RefuseOpenData(
    Initial: PartArchiveState,
    Geometry: SketchGeometry,
    SlotValue: int,
    Identity: int,
    ViewValue: PadDimView,
    Earlier: int,
    Opening: bytes,
    LinkValue: bytes,
    FinalState: PartArchiveState,
) -> int:
    TextX, TextY, TextZ = ViewValue.TextWorld
    BadViews = (
        Replace(ViewValue, SketchIndex=Earlier),
        Replace(ViewValue, VisualIndex=ViewValue.VisualIndex + 1),
        Replace(ViewValue, PlaneOrigin=(0, 0, 0.012)),
        Replace(ViewValue, PlaneNormal=(0, 0, -1)),
        Replace(ViewValue, TextWorld=(TextX, TextY, TextZ + 0.003)),
        Replace(ViewValue, TextWorld=(float("nan"), TextY, TextZ)),
    )
    BadCalls = tuple((SlotValue, Identity, Altered) for Altered in BadViews) + (
        ((SlotValue + 1) % 4, Identity, ViewValue),
        (SlotValue, Identity + 1, ViewValue),
    )
    for Slot, Dimension, Altered in BadCalls:
        try:
            EncodePadDimOpen(KConfigGen, Initial, Geometry, Slot, Dimension, Altered)
        except ArchiveError:
            continue
        raise ValueError("Constructor accepted a contradictory opening owner or frame")
    for Foreign in (
        LinkValue[:-6] + EncodeObjectRef(Earlier) + PackFields("<i", SlotValue),
        LinkValue[:-4] + PackFields("<i", (SlotValue + 1) % 4),
    ):
        try:
            VerifyOpenLink(Opening, Foreign, Initial, FinalState, ViewValue, SlotValue)
        except ArchiveError:
            continue
        raise ValueError("Typed readback accepted a contradictory adjacent owner")
    return len(BadCalls) + 2


# the scoped digest lets the evidence be compared without publishing native sources
def ReportPadOpen(Directory: FilePath) -> dict[str, object]:
    Directory = Directory.resolve(strict=True)
    Native = AuditDiscovery(Directory, KRepository, *KCapturePins, True)
    Evidence = ReadJsonPin(Directory / "report.json", KCapturePins[1])
    return {
        "application_build": Native["application_build"],
        "native_report_sha256": KCapturePins[1],
        "healthy_stock_controls": Native["stock_controls"],
        "native_observations": Native["verified_native_observations"],
        "licensed_archives": {
            Case["variant"]: ReplayDimOpen(Directory, Case)
            for Case in Evidence["observations"]["cases"]
        },
        "fresh_control": CheckOpenTrial(),
    }


# the replay command reads the retained evidence directory without writing to it
def RunPadDimOpen() -> None:
    Parser = ArgumentParser(description=__doc__)
    Parser.add_argument("--run-directory", required=True, type=FilePath)
    print(DumpJson(ReportPadOpen(Parser.parse_args().run_directory), sort_keys=True))


if __name__ == "__main__":
    RunPadDimOpen()
