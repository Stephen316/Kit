# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Verify the matched-owner component prefix against retained two-pad evidence."""

from argparse import ArgumentParser
from dataclasses import replace as Replace
from hashlib import sha256 as ShaValue
from json import dumps as DumpJson
from pathlib import Path as FilePath
import sys

# the offline runner uses the declared source tree and retained custody tools
KRepository = FilePath(__file__).resolve().parents[4]

# the source readers stay separate from the published package
sys.path[:0] = [
    str(KRepository / Lane)
    for Lane in (
        "src",
        "re/automation",
        "re/automation/TwoPad",
        "re/solidworks/WriterResearch",
        "re/solidworks/WriterResearch/TwoPadAtoms",
    )
]

from BossChoice import WriteChoiceCap
from BossOpen import KBossClass
from ConfigAtomManager import (
    BossAtomBody,
    ConfigAtomBinding,
    ReadBossAtom,
    WriteBossAtom,
)
from ConfigRoot import OpenConfigRoot
from LocalComponent import KComponentTail, KPartClass, KUnitComponent
from PadReceipts import ReadPadBytes
from PartArchive import PartArchiveState, PartArchiveWriter
from PilotEvidence import pinned_record as ReadJsonPin
from RectangleTrim import KReferenceClass
from VerifyDiscovery import AuditDiscovery
from VerifyPadCap import KCapturePins, OpenCapLane, TakeCapState
from WritePadAtoms import PadAtomBindings, ReadPadAtoms
from WritePadComp import EncodePadComp, KCompFaceClass, KMatchedAtomFlag, PadCompMatch
from convert.adapters.solidworks.Config.ModelEntry import ReadModelEntry
from convert.adapters.solidworks.Config.RootLayout import KConfigGen, LoadPartLayouts
from convert.adapters.solidworks.Container.Archive import (
    ArchiveError,
    KClassRefKind,
    KDefinitionKind,
)
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import (
    ArchiveCursor,
    FieldCursor,
)
from convert.adapters.solidworks.Container.Cmgr import KExtObjectClass
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.LocalFrame import ReadLocalPart
from convert.adapters.solidworks.Resolved.BossChooser import (
    ChooserOwner,
    ReadCap,
    SavedCap,
)
from convert.adapters.solidworks.Resolved.FaceIdentity import ReadFaceHead
from convert.adapters.solidworks.Resolved.TwoPad.PadHistory import ReadPadHistory


# the matched branch words belong to the component reference after its local unit
def ReadCompWords(Cursor: ArchiveCursor) -> tuple[int, int]:
    Cursor.TakePointer((KCompFaceClass,), KDefinitionKind, CompactOnly=True)
    Fields = FieldCursor(Cursor.BlobValue, Cursor.Offset)
    _, PartObject = ReadLocalPart(Cursor, KConfigGen)
    Fields.ReadInts("<2HB")
    Words = Fields.ReadInts("<20i")
    AtomId = Words[1]
    RequireArch(
        Words,
        (KMatchedAtomFlag, AtomId, AtomId, 0, *KComponentTail, KConfigGen),
        "matched component reference words",
    )
    RequireArch(AtomId > 0, True, "positive matched component atom")
    RequireArch(Fields.Offset, Cursor.Offset, "same typed local reference return")
    RequireArch(Cursor.ReadInts("<B"), (0,), "absent component face alias")
    return PartObject, AtomId


# independent configured allocations provide the earlier atom and distinct upper control
def ReadCompAtoms(ConfigData: bytes) -> PadAtomBindings:
    Model, _ = ReadModelEntry(ConfigData, LoadPartLayouts())
    _, Split = OpenConfigRoot(ConfigData)
    Cursor = ArchiveCursor(
        ConfigData, Split + 4, Model.Counter, Model.Classes, Model.Objects
    )
    return ReadPadAtoms(Cursor, KConfigGen)


# the existing typed reader checks the same allocation state and every emitted word
def VerifyCompData(
    DataValue: bytes,
    Initial: PartArchiveState,
    FinalState: PartArchiveState,
    MatchValue: PadCompMatch,
) -> None:
    Cursor = Initial.Cursor(DataValue, 0)
    RequireArch(
        ReadCompWords(Cursor),
        (MatchValue.PartObject, MatchValue.AtomId),
        "fresh matched part and source atom",
    )
    RequireArch(Cursor.Offset, len(DataValue), "closed component prefix")
    RequireArch(TakeCapState(Cursor), FinalState, "exact component allocation state")


# follow the complete resolved owner and reproduce only its independent prefix
def ReplayCompSave(Directory: FilePath, Capture: dict) -> dict[str, object]:
    SaveValue = Capture["save"]
    Archive = SldprtArchive.from_bytes(
        ReadPadBytes(Directory, SaveValue["file"], SaveValue["sha256"])
    )
    ConfigData = Archive.require("Contents/Config-0")
    Resolved = Archive.require("Contents/Config-0-ResolvedFeatures")
    Atoms = ReadCompAtoms(ConfigData)
    History = ReadPadHistory(ConfigData, Resolved)
    Later, Owner, CapValue, _ = OpenCapLane(ConfigData, Resolved)
    Component = History.Support["face"]["component"]
    RequireArch(
        (Atoms.Base.ObjectIndex, Atoms.Upper.ObjectIndex),
        (History.BaseValue["transfer_object"], History.UpperValue["transfer_object"]),
        "independently resolved configured transfer ownership",
    )
    FirstIndex = Component["object_index"] - 1
    Initial = PartArchiveState(
        FirstIndex,
        tuple(
            sorted(
                (Index, Name)
                for Index, Name in Later.Classes.items()
                if Index < FirstIndex
            )
        ),
        tuple(
            sorted(
                (Index, Name)
                for Index, Name in Later.Objects.items()
                if Index < FirstIndex
            )
        ),
    )
    Start = Component["offset"]
    Cursor = Initial.Cursor(Resolved, Start)
    PartObject, AtomId = ReadCompWords(Cursor)
    RequireArch(
        PartObject, History.Support["part_object"], "same enclosing local support part"
    )
    MatchValue = PadCompMatch(
        PartObject,
        CapValue["object_index"],
        History.BaseValue["transfer_object"],
        AtomId,
    )
    StopValue = Cursor.Offset
    Observed = TakeCapState(Cursor)
    ReadFaceHead(Cursor, KClassRefKind, 512)
    RequireArch(Cursor.Offset, Later.Offset, "same completed face header boundary")
    RequireArch(
        TakeCapState(Cursor), TakeCapState(Later), "same reached face header state"
    )
    DataValue, FinalState = EncodePadComp(
        KConfigGen, Initial, PartObject, Owner, CapValue, Atoms.Base, MatchValue
    )
    RequireArch(
        DataValue == Resolved[Start:StopValue], True, "exact saved component prefix"
    )
    RequireArch(FinalState, Observed, "same saved component allocations")
    VerifyCompData(DataValue, Initial, FinalState, MatchValue)
    return {
        "archive_sha256": SaveValue["sha256"],
        "record_sha256": ShaValue(DataValue).hexdigest(),
        "record_bytes": len(DataValue),
        "allocations": [Initial.NextIndex, FinalState.NextIndex],
        "source_atom": AtomId,
    }


# an independently typed atom pair differentiates the selected owner from another one
def BuildTrialAtoms(
    Writer: PartArchiveWriter,
) -> tuple[ConfigAtomBinding, ConfigAtomBinding]:
    Prefix = Writer.Snapshot()
    Start = len(Writer.Build())
    Base = WriteBossAtom(Writer, 271, BossAtomBody(74, 5103))
    Other = WriteBossAtom(Writer, 272, BossAtomBody(83, 5103), Flags=1)
    DataValue = Writer.Build()[Start:]
    Cursor = Prefix.Cursor(DataValue, 0)
    RequireArch(ReadBossAtom(Cursor, 271), Base, "fresh selected source atom")
    RequireArch(ReadBossAtom(Cursor, 272, Flags=1), Other, "fresh different atom")
    RequireArch(Cursor.Offset, len(DataValue), "fresh atom records return")
    RequireArch(TakeCapState(Cursor), Writer.Snapshot(), "fresh typed atom allocations")
    return Base, Other


# fresh filed part and earlier chooser slots provide a genuine owner preflight control
def BuildCompTrial() -> tuple[
    PartArchiveState,
    int,
    int,
    ChooserOwner,
    SavedCap,
    SavedCap,
    ConfigAtomBinding,
    ConfigAtomBinding,
]:
    Writer = PartArchiveWriter()
    Writer.BeginObject(KPartClass, 1)
    PartObject = Writer.next_index - 1
    Writer.BeginObject(KPartClass, 1)
    OtherPart = Writer.next_index - 1
    Writer.BeginObject(KUnitComponent, 1)
    Base, Other = BuildTrialAtoms(Writer)
    Writer.BeginObject(KExtObjectClass, 1)
    FileObject = Writer.next_index - 1
    Writer.BeginObject(KBossClass, 1)
    Owner: ChooserOwner = {
        "object_index": Writer.next_index - 1,
        "native_feature_id": Base.Body.FeatureId,
        "file_ref_object": FileObject,
    }
    Writer.BeginObject(KReferenceClass, 1)
    Prefix = Writer.Snapshot()
    Chooser = PartArchiveWriter(Prefix)
    WriteChoiceCap(Chooser, KConfigGen, Owner, 0x01020304, 0, (9, 32, 26, 18))
    WriteChoiceCap(Chooser, KConfigGen, Owner, 0x01020304, 1, (32, 9, 18, 26))
    DataValue = Chooser.Build()
    Cursor = Prefix.Cursor(DataValue, 0)
    Bottom = ReadCap(Cursor, KDefinitionKind, 0, Owner)
    Top = ReadCap(Cursor, KClassRefKind, 1, Owner)
    StateValue = Chooser.Snapshot()
    RequireArch(Cursor.Offset, len(DataValue), "fresh chooser closes before support")
    RequireArch(TakeCapState(Cursor), StateValue, "fresh chooser allocations")
    return StateValue, PartObject, OtherPart, Owner, Top, Bottom, Base, Other


# independent changed binding and allocation controls each have a refusal boundary
def CheckCompTrial() -> dict[str, object]:
    StateValue, PartObject, OtherPart, Owner, Top, Bottom, Base, Other = (
        BuildCompTrial()
    )
    MatchValue = PadCompMatch(
        PartObject, Top["object_index"], Base.ObjectIndex, Base.AtomId
    )
    DataValue, FinalState = EncodePadComp(
        KConfigGen, StateValue, PartObject, Owner, Top, Base, MatchValue
    )
    VerifyCompData(DataValue, StateValue, FinalState, MatchValue)
    Preexisting = PartArchiveWriter(StateValue)
    Preexisting.BeginObject(KCompFaceClass, 1)
    Refusals = (
        (StateValue, PartObject, Top, Base, None),
        (StateValue, OtherPart, Top, Base, MatchValue),
        (StateValue, PartObject, Top, Base, Replace(MatchValue, PartObject=OtherPart)),
        (
            StateValue,
            PartObject,
            Top,
            Base,
            Replace(MatchValue, CapObject=Bottom["object_index"]),
        ),
        (
            StateValue,
            PartObject,
            Top,
            Base,
            Replace(MatchValue, TransferObject=Other.ObjectIndex),
        ),
        (StateValue, PartObject, Top, Base, Replace(MatchValue, AtomId=Other.AtomId)),
        (StateValue, PartObject, Top, Other, MatchValue),
        (StateValue, PartObject, Bottom, Base, MatchValue),
        (
            StateValue,
            PartObject,
            Top,
            Replace(Base, ObjectIndex=Owner["object_index"]),
            MatchValue,
        ),
        (Preexisting.Snapshot(), PartObject, Top, Base, MatchValue),
    )
    for State, Part, CapValue, SourceAtom, Evidence in Refusals:
        try:
            EncodePadComp(
                KConfigGen, State, Part, Owner, CapValue, SourceAtom, Evidence
            )
        except ArchiveError:
            continue
        raise ValueError("Constructor accepted a contradictory component owner")
    for Corrupt in (DataValue[:-1] + bytes([1]), DataValue + bytes(1)):
        try:
            VerifyCompData(Corrupt, StateValue, FinalState, MatchValue)
        except ArchiveError:
            continue
        raise ValueError("Reader accepted a contradictory component return")
    return {
        "record_bytes": len(DataValue),
        "record_sha256": ShaValue(DataValue).hexdigest(),
        "selected_atom": Base.AtomId,
        "other_atom": Other.AtomId,
        "allocations": [StateValue.NextIndex, FinalState.NextIndex],
        "negative_controls": len(Refusals) + 2,
    }


# private evidence is reported using exact digests and bounded role counts
def ReportPadComp(Directory: FilePath) -> dict[str, object]:
    Directory = Directory.resolve(strict=True)
    Native = AuditDiscovery(Directory, KRepository, *KCapturePins, True)
    ReportValue = ReadJsonPin(Directory / "report.json", KCapturePins[1])
    return {
        "application_build": Native["application_build"],
        "native_report_sha256": KCapturePins[1],
        "healthy_stock_controls": Native["stock_controls"],
        "native_observations": Native["verified_native_observations"],
        "licensed_archives": {
            Capture["variant"]: ReplayCompSave(Directory, Capture)
            for Capture in ReportValue["observations"]["cases"]
        },
        "fresh_control": CheckCompTrial(),
    }


# the explicit offline entry point consumes only the retained evidence directory
def RunPadComp() -> None:
    Parser = ArgumentParser(description=__doc__)
    Parser.add_argument("--run-directory", required=True, type=FilePath)
    print(DumpJson(ReportPadComp(Parser.parse_args().run_directory), sort_keys=True))


if __name__ == "__main__":
    RunPadComp()
