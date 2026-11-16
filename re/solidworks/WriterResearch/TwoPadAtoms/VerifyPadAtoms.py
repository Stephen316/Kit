# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Reproduce the configured atom manager on the sealed licensed two-pad saves."""

from argparse import ArgumentParser
from hashlib import sha256
from json import dumps as DumpJson
from pathlib import Path
from struct import pack_into as PackInto
import sys

# the verifier reads the existing archive and licensed evidence helpers in place
KRepository = Path(__file__).resolve().parents[4]

# resolve the private replay dependencies from this source checkout
sys.path[:0] = [
    str(KRepository / "src"),
    str(KRepository / "re/automation"),
    str(KRepository / "re/automation/TwoPad"),
    str(KRepository / "re/solidworks/WriterResearch"),
]

from ConfigMaterial import KModelDataClass
from ConfigRoot import OpenConfigRoot
from PadReceipts import ReadPadBytes
from PartArchive import PartArchiveWriter
from VerifyConfigResolvedFraming import allocation_state
from VerifyDiscovery import AuditDiscovery
from WritePadAtoms import PadAtomOwners, ReadPadAtoms, WritePadAtoms
from convert.adapters.solidworks.Config.ModelEntry import ReadModelEntry
from convert.adapters.solidworks.Config.OrdinaryMap import ReadRelEntry, SkipAtomList
from convert.adapters.solidworks.Config.RootAtoms import AtomEnd, EndGhosts
from convert.adapters.solidworks.Config.RootFields import ModelAtomStart
from convert.adapters.solidworks.Config.RootLayout import KConfigGen, LoadPartLayouts
from convert.adapters.solidworks.Container.Archive import ArchiveError, ReadTag
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Resolved.TwoPad.PadHistory import ReadPadHistory


# the resolved history and trailing map independently bind the generated occurrences
def CheckArchive(Data: bytes) -> dict[str, object]:
    Archive = SldprtArchive.from_bytes(Data)
    Config = Archive.require("Contents/Config-0")
    Proof = ReadPadHistory(
        Config, Archive.require("Contents/Config-0-ResolvedFeatures")
    )
    Layouts = LoadPartLayouts()
    Model, _ = ReadModelEntry(Config, Layouts)
    _, Split = OpenConfigRoot(Config)
    Start = Split + 4
    Cursor = ArchiveCursor(Config, Start, Model.Counter, Model.Classes, Model.Objects)
    Initial = allocation_state(Cursor)
    Saved = ReadPadAtoms(Cursor, KConfigGen)

    Base = Proof.BaseValue
    Upper = Proof.UpperValue
    RequireArch(
        (Saved.Base.ObjectIndex, Saved.Upper.ObjectIndex, Saved.Base.ObjectIndex),
        (
            Base["transfer_object"],
            Upper["transfer_object"],
            Upper["parent_transfer_object"],
        ),
        "resolved configured atom occurrences",
    )
    RequireArch(Saved.Upper.AtomId, Upper["atom_id"], "resolved upper atom identity")
    Owners = PadAtomOwners(
        Base["native_feature_id"],
        Upper["native_feature_id"],
        Saved.Upper.Body.SolidBodyTag,
    )
    Writer = PartArchiveWriter(Initial)
    Fresh = WritePadAtoms(Writer, KConfigGen, Owners)
    DataValue = Writer.build()
    RequireArch(Fresh, Saved, "fresh bindings agree with resolved owners")
    RequireArch(DataValue, Config[Start : Cursor.Offset], "generated manager bytes")
    RequireArch(Writer.Snapshot(), allocation_state(Cursor), "generated manager map")

    # an independent complete read validates the manager and ghost boundaries
    _, AtomStart, Count = ModelAtomStart(Config, Model)
    Relation, RelationCount = ReadRelEntry(Config, Layouts, (2,))
    RequireArch(
        (Count, Cursor.Offset, EndGhosts(Config, Cursor.Offset), Relation.Counter),
        (
            RelationCount,
            SkipAtomList(Config, AtomStart, Count) + 4,
            Relation.offset,
            Cursor.NextIndex + 2,
        ),
        "independently reached relation boundary and allocation",
    )
    RequireArch(
        {
            Index: Class
            for Index, Class in Relation.Objects.items()
            if Index < Cursor.NextIndex
        },
        Cursor.Objects,
        "configured occurrences retained by the independent relation reader",
    )
    FreshCursor = Initial.Cursor(DataValue, 0)
    RequireArch(ReadPadAtoms(FreshCursor, KConfigGen), Fresh, "fresh manager readback")
    RequireArch(FreshCursor.Offset, len(DataValue), "complete fresh manager readback")
    return {
        "offset": Start,
        "size_bytes": len(DataValue),
        "relation_manager_offset": Relation.offset,
        "next_archive_slot": Cursor.NextIndex,
        "native_feature_ids": [Owners.BaseFeature, Owners.UpperFeature],
        "atom_ids": [Fresh.Base.AtomId, Fresh.Upper.AtomId],
        "archive_occurrences": [Fresh.Base.ObjectIndex, Fresh.Upper.ObjectIndex],
        "shared_solid_tag": Owners.MergedSolidTag,
        "sha256": sha256(DataValue).hexdigest(),
    }


# distinct new identities and a new map reject any replay of saved identifiers
def CheckFresh() -> tuple[str, int]:
    Writer = PartArchiveWriter()
    Writer.BeginObject(KModelDataClass, 1)
    Initial = Writer.Snapshot()
    Owners = PadAtomOwners(73, 118, 41023)
    Writer = PartArchiveWriter(Initial)
    Fresh = WritePadAtoms(Writer, KConfigGen, Owners)
    DataValue = Writer.build()
    Cursor = Initial.Cursor(DataValue, 0)
    RequireArch(ReadPadAtoms(Cursor, KConfigGen), Fresh, "fresh typed bindings")
    RequireArch(
        (Fresh.Upper.ObjectIndex, Fresh.Base.ObjectIndex, Cursor.Offset),
        (Initial.NextIndex + 1, Initial.NextIndex + 2, len(DataValue)),
        "fresh archive allocation order",
    )

    Rejected = 0
    for Invalid in (
        PadAtomOwners(73, 73, 41023),
        PadAtomOwners(0, 118, 41023),
        PadAtomOwners(73, 118, 0),
        PadAtomOwners(73, 118, 0x80000000),
    ):
        Refused = PartArchiveWriter(Initial)
        try:
            WritePadAtoms(Refused, KConfigGen, Invalid)
        except ArchiveError:
            RequireArch(
                (Refused.Snapshot(), Refused.build()), (Initial, b""), "atomic refusal"
            )
            Rejected += 1
        else:
            raise ArchiveError("accepted invalid pad atom owners")

    First = 14
    Second = AtomEnd(DataValue, First + ReadTag(DataValue, First).size)
    End = AtomEnd(DataValue, Second + ReadTag(DataValue, Second).size)
    for Changes in (
        ((6, 103),),
        ((10, 1),),
        ((Second - 52, 101),),
        ((End - 48, 0),),
        ((End - 44, 118), (End - 40, 118)),
        ((End - 16, 41024), (End - 8, 41024)),
        ((End, KConfigGen - 1),),
    ):
        Altered = bytearray(DataValue)
        for Offset, Value in Changes:
            PackInto("<i", Altered, Offset, Value)
        try:
            ReadPadAtoms(Initial.Cursor(bytes(Altered), 0), KConfigGen)
        except ArchiveError:
            Rejected += 1
        else:
            raise ArchiveError("accepted a mutated two-pad manager")
    return sha256(DataValue).hexdigest(), Rejected


# verify native custody and compare the generated spans without opening an application
def RunVerification() -> None:
    Parser = ArgumentParser(description=__doc__)
    Parser.add_argument("--run-directory", required=True, type=Path)
    Parser.add_argument("--source-revision", required=True)
    Parser.add_argument("--report-sha256", required=True)
    Parser.add_argument("--authoring-sha256", required=True)
    Parser.add_argument("--reopen-sha256", required=True)
    Args = Parser.parse_args()
    Native = AuditDiscovery(
        Args.run_directory,
        KRepository,
        Args.source_revision,
        Args.report_sha256,
        Args.authoring_sha256,
        Args.reopen_sha256,
        True,
    )
    Cases = {
        Case["variant"]: CheckArchive(
            ReadPadBytes(
                Args.run_directory, f"{Case['variant']}.SLDPRT", Case["archive_sha256"]
            )
        )
        for Case in Native["cases"]
    }
    Fresh, Rejected = CheckFresh()
    Report = {
        "capture_source_revision": Native["capture_source_revision"],
        "native_report_sha256": Native["report_sha256"],
        "native_observations": Native["verified_native_observations"],
        "stock_controls": Native["stock_controls"],
        "cases": Cases,
        "fresh_sha256": Fresh,
        "refusals": Rejected,
    }
    Payload = DumpJson(Report, sort_keys=True, separators=(",", ":"), allow_nan=False)
    sys.stdout.buffer.write((Payload + "\n").encode("utf-8"))


if __name__ == "__main__":
    RunVerification()
