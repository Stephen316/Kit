# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Verify the upper-pad chain against its continuing typed profile and cap."""

from argparse import ArgumentParser
from dataclasses import replace as Replace
from hashlib import sha256 as ShaValue
from json import dumps as DumpJson
from pathlib import Path as FilePath
import sys

# direct replay ties the authored sources to the exact repository checkout
KRepository = FilePath(__file__).resolve().parents[4]

# explicit search roots support the standalone source and prior closed region writer
sys.path[:0] = [
    str(KRepository / Lane)
    for Lane in (
        "src",
        "re/automation",
        "re/automation/TwoPad",
        "re/solidworks/WriterResearch",
        "re/solidworks/WriterResearch/TwoPadSketch",
    )
]

from BossChoice import WriteChoiceCap
from BossOpen import KBossClass
from OriginSketch import KObjectList, KSketchClass
from PadReceipts import ReadPadBytes
from PartArchive import PartArchiveState, PartArchiveWriter
from PilotEvidence import pinned_record as ReadJsonPin
from RectangleCorners import KLineHandle
from RectangleRegion import KRegionClass
from RectangleSupport import KChainClass
from RectangleTrim import KReferenceClass
from VerifyDiscovery import AuditDiscovery
from VerifyPadCap import KCapturePins, TakeCapState
from WritePadChain import EncodePadChain, PadChainEdge
from WritePadRegion import EncodePadRegion
from convert.adapters.solidworks.Config.OrdinaryMap import ReadEmptyMap
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import ArchiveError, KDefinitionKind
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Cmgr import KExtObjectClass
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Resolved.BossChooser import (
    ChooserOwner,
    ReadCap,
    SavedCap,
)
from convert.adapters.solidworks.Resolved.ContourChain import ReadChain
from convert.adapters.solidworks.Resolved.ContourSurf import ProfileOwner
from convert.adapters.solidworks.Resolved.Cut.CutEdgeRef import CheckCutEdges
from convert.adapters.solidworks.Resolved.Cut.CutProfileBody import (
    CutProfileBody,
    ReadCutBody,
    ReadKernelMut,
)
from convert.adapters.solidworks.Resolved.FaceIdentity import SurfaceKey
from convert.adapters.solidworks.Resolved.ResolvedHead import OpenResolved
from convert.adapters.solidworks.Resolved.TwoPad.PadHistory import (
    KPadListCount,
    ReadBasePad,
    ReadPadSupport,
)
from convert.adapters.solidworks.Resolved.TwoPad.PadProfile import ReadPadProfMut
from convert.adapters.solidworks.Sketch.GeometryTypes import (
    SketchGeometry,
    SketchLine,
    SketchRelation,
)


# the real edge permutation and primary references bind each saved chain position
def JoinPadEdges(
    BodyValue: CutProfileBody, CapValue: SavedCap
) -> tuple[PadChainEdge, ...]:
    References = BodyValue["edge_references"]
    CheckCutEdges(References, CapValue)
    Ordered = tuple(References[Index - 1] for Index in BodyValue["edge_order"])
    return tuple(
        PadChainEdge(
            Identity,
            (*SurfaceKey(RefValue["primary"])[:3], RefValue["boundary_occurrences"][0]),
        )
        for Identity, RefValue in zip(
            BodyValue["chain"]["edge_ids"], Ordered, strict=True
        )
    )


# typed reading must close precisely before the next geometry selector
def VerifyChain(
    DataValue: bytes,
    Initial: PartArchiveState,
    FinalState: PartArchiveState,
    Projected: tuple[PadChainEdge, ...],
) -> None:
    Cursor = Initial.Cursor(DataValue, 0)
    RequireArch(Cursor.ReadInts("<Ii"), (1, 1), "one inherited upper profile chain")
    Chain = ReadChain(Cursor)
    RequireArch(
        Chain["edge_ids"],
        tuple(Edge.NativeId for Edge in Projected),
        "same projected id order",
    )
    RequireArch(Cursor.Offset, len(DataValue), "exact projected chain boundary")
    RequireArch(
        TakeCapState(Cursor), FinalState, "complete projected chain allocations"
    )


# reopen the independently typed profile continuation on the same earlier cap
def ReplayPadChain(Directory: FilePath, Capture: dict) -> dict[str, object]:
    SaveValue = Capture["save"]
    Archive = SldprtArchive.from_bytes(
        ReadPadBytes(Directory, SaveValue["file"], SaveValue["sha256"])
    )
    ConfigData = Archive.require("Contents/Config-0")
    Resolved = Archive.require("Contents/Config-0-ResolvedFeatures")
    Mapping, _ = ReadEmptyMap(ConfigData, (2,))
    Cursor = OpenResolved(Resolved, Mapping, KPadListCount)
    BossOwner, BossEnd = ReadBasePad(Cursor)
    Profile, _ = ReadPadProfMut(Cursor)
    CapValue = BossOwner["choosers"]["caps"][1]
    Initial = TakeCapState(Cursor)
    Start = Cursor.Offset
    Prefix = Initial.Cursor(Resolved, Start)
    RequireArch(Prefix.ReadInts("<Ii"), (1, 1), "one saved projected chain")
    Chain = ReadChain(Prefix)
    StopValue = Prefix.Offset
    Observed = TakeCapState(Prefix)
    KernelValue = ReadKernelMut(Prefix)
    BodyValue = ReadCutBody(Cursor, Profile.SketchIndex)
    Support = ReadPadSupport(
        Initial.Cursor(Resolved, Start), Profile, BossOwner, BossEnd
    )
    RequireArch(
        BodyValue["support_offset"],
        Support["offset"],
        "same typed support continuation",
    )
    RequireArch(
        (BodyValue["chain"], BodyValue["kernel_packet"]),
        (Chain, KernelValue),
        "the following kernel packet has a separate boundary",
    )
    Owner: ProfileOwner = {
        "profile_object": Profile.ObjectIndex,
        "native_feature_id": Profile.FeatureId,
    }
    Projected = JoinPadEdges(BodyValue, CapValue)
    DataValue, FinalState = EncodePadChain(
        KConfigGen, Initial, Owner, Profile.Geometry, BossOwner, CapValue, Projected
    )
    RequireArch(
        DataValue == Resolved[Start:StopValue], True, "exact inherited projected chain"
    )
    RequireArch(FinalState, Observed, "same complete saved chain state")
    VerifyChain(DataValue, Initial, FinalState, Projected)
    return {
        "archive_sha256": SaveValue["sha256"],
        "record_bytes": len(DataValue),
        "record_sha256": ShaValue(DataValue).hexdigest(),
        "allocations": [Initial.NextIndex, FinalState.NextIndex],
        "cap_side_order": [Edge.CapSide[-1] for Edge in Projected],
        "projected_ids": [Edge.NativeId for Edge in Projected],
        "following_kernel_bytes": KernelValue["size"],
    }


# generate the earlier chooser independently from the fresh projected edge ids
def BuildChainCap() -> tuple[PartArchiveState, ChooserOwner, SavedCap, int]:
    Writer = PartArchiveWriter()
    Writer.BeginObject("moPart_c", 1)
    Writer.BeginObject(KExtObjectClass, 1)
    FileIndex = Writer.next_index - 1
    Writer.BeginObject(KExtObjectClass, 1)
    ForeignFile = Writer.next_index - 1
    for Name in (
        KSketchClass,
        KObjectList,
        KRegionClass,
        KLineHandle,
        KChainClass,
        KBossClass,
    ):
        Writer.BeginObject(Name, 1)
    Owner: ChooserOwner = {
        "object_index": Writer.next_index - 1,
        "native_feature_id": 74,
        "file_ref_object": FileIndex,
    }
    Writer.BeginObject(KReferenceClass, 1)
    Initial = Writer.Snapshot()
    CapWriter = PartArchiveWriter(Initial)
    WriteChoiceCap(CapWriter, KConfigGen, Owner, 0x01020304, 1, (32, 9, 18, 26))
    Earlier = CapWriter.Build()
    Cursor = Initial.Cursor(Earlier, 0)
    CapValue = ReadCap(Cursor, KDefinitionKind, 1, Owner)
    StateValue = CapWriter.Snapshot()
    RequireArch(Cursor.Offset, len(Earlier), "exact earlier chooser return")
    RequireArch(TakeCapState(Cursor), StateValue, "complete earlier chooser map")
    return StateValue, Owner, CapValue, ForeignFile


# the fresh upper rectangle closes with its own allocated local region
def BuildChainLocal(
    StateValue: PartArchiveState,
) -> tuple[PartArchiveState, ProfileOwner, SketchGeometry]:
    Writer = PartArchiveWriter(StateValue)
    Writer.BeginObject("moProfileFeature_c", 1)
    Profile: ProfileOwner = {
        "profile_object": Writer.next_index - 1,
        "native_feature_id": 87,
    }
    Writer.BeginObject(KSketchClass, 1)
    SketchIndex = Writer.next_index - 1
    Lines: list[SketchLine] = []
    Axes: list[SketchRelation] = []
    for Ordinal, (Identity, Endpoints, Code, Kind) in enumerate(
        (
            (101, [0, 3], 5, "vertical"),
            (102, [0, 1], 4, "horizontal"),
            (103, [1, 2], 5, "vertical"),
            (104, [3, 2], 4, "horizontal"),
        ),
        start=1,
    ):
        Handle = Writer.next_index
        Writer.BeginObject(KLineHandle, 1)
        Lines.append(
            {
                "member_index": Ordinal,
                "native_id": Identity,
                "flags": 4,
                "point_indices": Endpoints,
            }
        )
        Axes.append(
            {
                "start": 0,
                "end": 0,
                "line_handle_object": Handle,
                "line_handle_fields": (Identity, -1, 0),
                "segment_native_id": Identity,
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
    _, FinalState = EncodePadRegion(
        KConfigGen, Writer.Snapshot(), Geometry, (101, 102, 103, 104)
    )
    return FinalState, Profile, Geometry


# contradictory projected owner and order controls must refuse before any result
def CheckBadChains(
    Initial: PartArchiveState,
    Profile: ProfileOwner,
    Geometry: SketchGeometry,
    BossOwner: ChooserOwner,
    CapValue: SavedCap,
    Projected: tuple[PadChainEdge, ...],
    ForeignFile: int,
) -> int:
    First, Second, Third, Fourth = Projected
    WrongFile = (ForeignFile, *First.CapSide[1:])
    WrongClock = (
        First.CapSide[0],
        First.CapSide[1],
        First.CapSide[2] + 1,
        First.CapSide[3],
    )
    Controls = (
        (First, Replace(Second, NativeId=First.NativeId), Third, Fourth),
        (Replace(First, NativeId=101), Second, Third, Fourth),
        (Replace(First, NativeId=0x80000000), Second, Third, Fourth),
        (Second, First, Third, Fourth),
        (Replace(First, CapSide=WrongFile), Second, Third, Fourth),
        (Replace(First, CapSide=WrongClock), Second, Third, Fourth),
    )
    for Altered in Controls:
        try:
            EncodePadChain(
                KConfigGen, Initial, Profile, Geometry, BossOwner, CapValue, Altered
            )
        except ArchiveError:
            continue
        raise ValueError("Constructor accepted a contradictory projected edge")
    return len(Controls)


# changed chooser and sketch allocations keep the two edge namespaces distinct
def CheckChainTrial() -> dict[str, object]:
    Prior, BossOwner, CapValue, ForeignFile = BuildChainCap()
    Initial, Profile, Geometry = BuildChainLocal(Prior)
    Projected = tuple(
        PadChainEdge(Identity, SurfaceKey(EdgeValue))
        for Identity, EdgeValue in zip(
            (44, 61, 82, 105), CapValue["edges"], strict=True
        )
    )
    DataValue, FinalState = EncodePadChain(
        KConfigGen, Initial, Profile, Geometry, BossOwner, CapValue, Projected
    )
    VerifyChain(DataValue, Initial, FinalState, Projected)
    Negative = CheckBadChains(
        Initial, Profile, Geometry, BossOwner, CapValue, Projected, ForeignFile
    )
    try:
        EncodePadChain(
            KConfigGen, FinalState, Profile, Geometry, BossOwner, CapValue, Projected
        )
    except ArchiveError:
        Negative += 1
    else:
        raise ValueError("Constructor accepted a second chain at the completed station")
    for Altered in (DataValue[:-1] + bytes([1]), DataValue + bytes(1)):
        try:
            VerifyChain(Altered, Initial, FinalState, Projected)
        except ArchiveError:
            continue
        raise ValueError("Reader accepted a contradictory projected chain return")
    return {
        "record_bytes": len(DataValue),
        "record_sha256": ShaValue(DataValue).hexdigest(),
        "allocations": [Initial.NextIndex, FinalState.NextIndex],
        "cap_side_order": [Edge.CapSide[-1] for Edge in Projected],
        "projected_ids": [Edge.NativeId for Edge in Projected],
        "negative_controls": Negative + 2,
    }


# the digest report binds only the already sealed native inputs and scoped output
def ReportPadChain(Directory: FilePath) -> dict[str, object]:
    Directory = Directory.resolve(strict=True)
    Native = AuditDiscovery(Directory, KRepository, *KCapturePins, True)
    Evidence = ReadJsonPin(Directory / "report.json", KCapturePins[1])
    return {
        "application_build": Native["application_build"],
        "native_report_sha256": KCapturePins[1],
        "healthy_stock_controls": Native["stock_controls"],
        "native_observations": Native["verified_native_observations"],
        "licensed_archives": {
            Case["variant"]: ReplayPadChain(Directory, Case)
            for Case in Evidence["observations"]["cases"]
        },
        "fresh_control": CheckChainTrial(),
    }


# the explicit command reads a private directory without writing generated native files
def RunPadChain() -> None:
    Parser = ArgumentParser(description=__doc__)
    Parser.add_argument("--run-directory", required=True, type=FilePath)
    print(DumpJson(ReportPadChain(Parser.parse_args().run_directory), sort_keys=True))


if __name__ == "__main__":
    RunPadChain()
