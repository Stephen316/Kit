# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Verify the bounded upper-pad cap occurrence using sealed discovery inputs."""

from argparse import ArgumentParser
from hashlib import sha256 as ShaValue
from json import dumps as DumpJson
from pathlib import Path as FilePath
import sys

# the offline verifier resolves its sibling research and custody helpers
KRepository = FilePath(__file__).resolve().parents[4]

# the sealed capture is validated with existing readers in their own source paths
sys.path[:0] = [
    str(KRepository / Lane)
    for Lane in (
        "src",
        "re/automation",
        "re/automation/TwoPad",
        "re/solidworks/WriterResearch",
    )
]

from BossChoice import WriteChoiceCap
from BossOpen import KBossClass
from PadReceipts import ReadPadBytes
from PartArchive import PartArchiveState, PartArchiveWriter
from PilotEvidence import pinned_record as ReadJsonPin
from RectangleTrim import KReferenceClass
from VerifyDiscovery import AuditDiscovery
from WritePadCap import EncodePadCap
from convert.adapters.solidworks.Config.OrdinaryMap import ReadEmptyMap
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import (
    ArchiveError,
    KClassRefKind,
    KDefinitionKind,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Cmgr import KExtObjectClass
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.LocalFrame import ReadLocalPart
from convert.adapters.solidworks.Resolved.BossChooser import (
    ChooserOwner,
    ReadCap,
    SavedCap,
)
from convert.adapters.solidworks.Resolved.Cut.CutEdgeRef import CheckCutEdges
from convert.adapters.solidworks.Resolved.Cut.CutProfileBody import ReadCutBody
from convert.adapters.solidworks.Resolved.FaceIdentity import (
    KCapClass,
    KEdgeClass,
    ReadFaceHead,
    ReadFaceReturn,
    ReadSurfaceId,
    SurfaceKey,
)
from convert.adapters.solidworks.Resolved.ResolvedHead import OpenResolved
from convert.adapters.solidworks.Resolved.Support.FaceFrame import (
    CloseFaceFrame,
    FaceFrame,
    ReadFaceFrame,
)
from convert.adapters.solidworks.Resolved.Support.SupportPlane import ReadPlaneBody
from convert.adapters.solidworks.Resolved.TwoPad.PadHistory import (
    KPadListCount,
    ReadBasePad,
)
from convert.adapters.solidworks.Resolved.TwoPad.PadProfile import ReadPadProfMut

# the source and separate process receipts bind five curated licensed saves
KCapturePins = (
    "463a3de14e4cb34aeeaa6aed1aa1e8b2804572c8",
    "bf0d74c06878c6c5063e4b9a55c61c2ef258bdc24323adbfb8f8d069bc77697e",
    "7c25ed3111ec45d9646e7b5de9df16f90f57528d3f2b97fc4e14f2666a2a884f",
    "1ebdcdc23d4d220d549573dfb2c0cb45b1697ec7e42c192a3fb95bd34ba5699b",
)


# preservation of every allocation is stronger than comparing the counter alone
def TakeCapState(Cursor: ArchiveCursor) -> PartArchiveState:
    return PartArchiveState(
        Cursor.NextIndex,
        tuple(sorted(Cursor.Classes.items())),
        tuple(sorted(Cursor.Objects.items())),
    )


# the closed lane starts only after the typed component and face header read
def OpenCapLane(
    ConfigData: bytes,
    Resolved: bytes,
) -> tuple[ArchiveCursor, ChooserOwner, SavedCap, FaceFrame]:
    Mapping, _ = ReadEmptyMap(ConfigData, (2,))
    Cursor = OpenResolved(Resolved, Mapping, KPadListCount)
    Owner, _ = ReadBasePad(Cursor)
    CapValue = Owner["choosers"]["caps"][1]
    Profile, _ = ReadPadProfMut(Cursor)
    BodyValue = ReadCutBody(Cursor, Profile.SketchIndex)
    CheckCutEdges(BodyValue["edge_references"], CapValue)
    Cursor.TakePointer(("moCompRefPlane_c",), KClassRefKind, CompactOnly=True)
    _, PartIndex = ReadLocalPart(Cursor, KConfigGen)
    RequireArch(Cursor.ReadInts("<iI")[0], -1, "embedded plane feature selection")
    Cursor.TakePointer(("moRefPlane_c",), KClassRefKind, CompactOnly=True)
    ReadPlaneBody(Cursor)
    Cursor.TakePointer(("moFaceRefPlnData_c",), KDefinitionKind, CompactOnly=True)
    Frame = ReadFaceFrame(Cursor)
    Cursor.TakePointer(("moCompFace_c",), KDefinitionKind, CompactOnly=True)
    _, Component = ReadLocalPart(Cursor, KConfigGen)
    RequireArch(Component, PartIndex, "same enclosing part")
    RequireArch(Cursor.ReadInts("<B"), (0,), "absent face alias")
    _, Count = ReadFaceHead(Cursor, KClassRefKind, 512)
    RequireArch(Count, 4, "four selected cap boundaries")
    return Cursor, Owner, CapValue, Frame


# the unchanged identity readers verify each ordered producer and the guarded return
def CheckCapLane(Cursor: ArchiveCursor, CapValue: SavedCap) -> None:
    Primary = ReadSurfaceId(Cursor, KCapClass, IsCap=True)
    Edges = tuple(ReadSurfaceId(Cursor, KEdgeClass) for _ in range(4))
    ReadFaceReturn(Cursor)
    Observed = tuple(map(SurfaceKey, (Primary, *Edges)))
    Expected = tuple(map(SurfaceKey, (CapValue["primary"], *CapValue["edges"])))
    RequireArch(Observed, Expected, "same reached top cap and ordered boundaries")


# isolated readback must account for the entire fresh slice and its state
def VerifyCapData(
    DataValue: bytes,
    Initial: PartArchiveState,
    FinalState: PartArchiveState,
    CapValue: SavedCap,
) -> None:
    Cursor = Initial.Cursor(DataValue, 0)
    CheckCapLane(Cursor, CapValue)
    RequireArch(Cursor.Offset, len(DataValue), "exact cap occurrence length")
    RequireArch(TakeCapState(Cursor), FinalState, "exact cap allocation state")


# the existing support wrapper can continue immediately after the scoped lane
def ReplayCapSave(Directory: FilePath, Capture: dict) -> dict[str, object]:
    SaveValue = Capture["save"]
    Archive = SldprtArchive.from_bytes(
        ReadPadBytes(Directory, SaveValue["file"], SaveValue["sha256"])
    )
    Resolved = Archive.require("Contents/Config-0-ResolvedFeatures")
    Cursor, Owner, CapValue, Frame = OpenCapLane(
        Archive.require("Contents/Config-0"), Resolved
    )
    Start = Cursor.Offset
    Initial = TakeCapState(Cursor)
    CheckCapLane(Cursor, CapValue)
    StopValue = Cursor.Offset
    Observed = TakeCapState(Cursor)
    Cursor.ReadNull()
    CloseFaceFrame(Cursor, Frame)
    RequireArch(Cursor.ReadInts("<i"), (0,), "face plane axis code")
    DataValue, FinalState = EncodePadCap(KConfigGen, Initial, Owner, CapValue)
    VerifyCapData(DataValue, Initial, FinalState, CapValue)
    RequireArch(
        DataValue == Resolved[Start:StopValue], True, "exact saved cap occurrence"
    )
    RequireArch(FinalState, Observed, "same complete saved allocation state")
    return {
        "archive_sha256": SaveValue["sha256"],
        "record_sha256": ShaValue(DataValue).hexdigest(),
        "record_bytes": len(DataValue),
        "allocations": [Initial.NextIndex, FinalState.NextIndex],
    }


# an independently generated chooser supplies different file feature and edge identities
def BuildCapTrial() -> tuple[PartArchiveState, ChooserOwner, SavedCap, int, int]:
    Writer = PartArchiveWriter()
    Writer.BeginObject("moPart_c", 1)
    Writer.BeginObject(KExtObjectClass, 1)
    FileIndex = Writer.next_index - 1
    Writer.BeginObject(KExtObjectClass, 1)
    ForeignFile = Writer.next_index - 1
    Writer.BeginObject(KBossClass, 1)
    EarlierBoss = Writer.next_index - 1
    Writer.BeginObject(KBossClass, 1)
    Owner: ChooserOwner = {
        "object_index": Writer.next_index - 1,
        "native_feature_id": 74,
        "file_ref_object": FileIndex,
    }
    Writer.BeginObject(KReferenceClass, 1)
    Prefix = Writer.Snapshot()
    Chooser = PartArchiveWriter(Prefix)
    WriteChoiceCap(Chooser, KConfigGen, Owner, 0x01020304, 0, (9, 32, 26, 18))
    WriteChoiceCap(Chooser, KConfigGen, Owner, 0x01020304, 1, (32, 9, 18, 26))
    Source = Chooser.Build()
    Cursor = Prefix.Cursor(Source, 0)
    ReadCap(Cursor, KDefinitionKind, 0, Owner)
    CapValue = ReadCap(Cursor, KClassRefKind, 1, Owner)
    StateValue = Chooser.Snapshot()
    RequireArch(Cursor.Offset, len(Source), "fresh earlier chooser return")
    RequireArch(TakeCapState(Cursor), StateValue, "fresh earlier chooser allocation")
    return StateValue, Owner, CapValue, ForeignFile, EarlierBoss


# modified typed inputs must be refused without allocating any output bytes
def CheckCapInputs(
    StateValue: PartArchiveState,
    Owner: ChooserOwner,
    CapValue: SavedCap,
    ForeignFile: int,
    EarlierBoss: int,
) -> int:
    Primary = CapValue["primary"]
    First, Second, Third, Fourth = CapValue["edges"]
    BadOwners: tuple[ChooserOwner, ...] = (
        {**Owner, "object_index": EarlierBoss},
        {**Owner, "file_ref_object": ForeignFile},
        {**Owner, "native_feature_id": 75},
    )
    BadCaps: tuple[SavedCap, ...] = (
        {**CapValue, "primary": {**Primary, "occurrence": 0}},
        {
            **CapValue,
            "edges": [{**First, "file_ref_object": ForeignFile}, Second, Third, Fourth],
        },
        {**CapValue, "edges": [{**First, "time_word": 123}, Second, Third, Fourth]},
        {**CapValue, "edges": [Second, First, Third, Fourth]},
        {
            **CapValue,
            "edges": [
                First,
                {**Second, "occurrence": First["occurrence"]},
                Third,
                Fourth,
            ],
        },
        {
            **CapValue,
            "edges": [
                {**First, "feature_ref_object": Second["feature_ref_object"]},
                Second,
                Third,
                Fourth,
            ],
        },
    )
    Controls = (
        *((KConfigGen, Value, CapValue) for Value in BadOwners),
        *((KConfigGen, Owner, Value) for Value in BadCaps),
        (KConfigGen - 1, Owner, CapValue),
    )
    for Generation, OwnerValue, FaceValue in Controls:
        try:
            EncodePadCap(Generation, StateValue, OwnerValue, FaceValue)
        except ArchiveError:
            continue
        raise ValueError("Constructor accepted a contradictory face owner or boundary")
    return len(Controls)


# a separate fresh packet checks both rejection of a bad return and exact length
def CheckCapTrial() -> dict[str, object]:
    StateValue, Owner, CapValue, ForeignFile, EarlierBoss = BuildCapTrial()
    DataValue, FinalState = EncodePadCap(KConfigGen, StateValue, Owner, CapValue)
    VerifyCapData(DataValue, StateValue, FinalState, CapValue)
    Negative = CheckCapInputs(StateValue, Owner, CapValue, ForeignFile, EarlierBoss)
    for Corrupt in (
        DataValue[:-1] + bytes([DataValue[-1] ^ 1]),
        DataValue + bytes(1),
    ):
        try:
            VerifyCapData(Corrupt, StateValue, FinalState, CapValue)
        except ArchiveError:
            continue
        raise ValueError("Reader accepted a contradictory cap occurrence return")
    return {
        "record_sha256": ShaValue(DataValue).hexdigest(),
        "record_bytes": len(DataValue),
        "source": SurfaceKey(CapValue["primary"]),
        "boundaries": [Edge["occurrence"] for Edge in CapValue["edges"]],
        "allocations": [StateValue.NextIndex, FinalState.NextIndex],
        "negative_controls": Negative + 2,
    }


# reports record bytes by digest while private source material stays read only
def ReportPadCap(Directory: FilePath) -> dict[str, object]:
    Directory = Directory.resolve(strict=True)
    Native = AuditDiscovery(Directory, KRepository, *KCapturePins, True)
    ReportValue = ReadJsonPin(Directory / "report.json", KCapturePins[1])
    return {
        "native_report_sha256": KCapturePins[1],
        "application_build": Native["application_build"],
        "healthy_stock_controls": Native["stock_controls"],
        "native_observations": Native["verified_native_observations"],
        "licensed_archives": {
            Capture["variant"]: ReplayCapSave(Directory, Capture)
            for Capture in ReportValue["observations"]["cases"]
        },
        "fresh_control": CheckCapTrial(),
    }


# the explicit offline entry point accepts only a retained evidence directory
def RunPadCap() -> None:
    Parser = ArgumentParser(description=__doc__)
    Parser.add_argument("--run-directory", required=True, type=FilePath)
    print(DumpJson(ReportPadCap(Parser.parse_args().run_directory), sort_keys=True))


if __name__ == "__main__":
    RunPadCap()
