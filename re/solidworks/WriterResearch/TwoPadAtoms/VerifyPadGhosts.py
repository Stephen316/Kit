# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from argparse import ArgumentParser
from hashlib import sha256
from json import dumps as DumpJson
from pathlib import Path
from struct import pack_into as PackInto
import sys

# resolve the verifier dependencies in this checkout rather than in the evidence directory
KRepository = Path(__file__).resolve().parents[4]

# use the existing licensed discovery and archive evidence commands in place
sys.path[:0] = [
    str(KRepository / "src"),
    str(KRepository / "re/automation"),
    str(KRepository / "re/automation/TwoPad"),
    str(KRepository / "re/solidworks/WriterResearch"),
]

from ConfigGhostRelation import ReadGhostRelationManagers, WriteGhostRelationManagers
from ConfigMaterial import KModelDataClass
from ConfigRoot import OpenConfigRoot
from PadReceipts import ReadPadBytes
from PartArchive import PartArchiveWriter
from VerifyConfigResolvedFraming import allocation_state
from VerifyDiscovery import AuditDiscovery
from WritePadAtoms import ReadPadAtoms
from convert.adapters.solidworks.Config.Detail import ReadDetailStart
from convert.adapters.solidworks.Config.ModelEntry import ReadModelEntry
from convert.adapters.solidworks.Config.OrdinaryMap import ReadEmptyRel, ReadRelEntry
from convert.adapters.solidworks.Config.RootAtoms import EndGhosts
from convert.adapters.solidworks.Config.RootLayout import KConfigGen, LoadPartLayouts
from convert.adapters.solidworks.Container.Archive import ArchiveError, ReadTag
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Container import SldprtArchive


# independently close the full relation map and following saved detail block
def CheckManagers(Data: bytes) -> dict[str, object]:
    Config = SldprtArchive.from_bytes(Data).require("Contents/Config-0")
    Layouts = LoadPartLayouts()
    Model, _ = ReadModelEntry(Config, Layouts)
    _, Split = OpenConfigRoot(Config)
    Cursor = ArchiveCursor(
        Config, Split + 4, Model.Counter, Model.Classes, Model.Objects
    )
    _ = ReadPadAtoms(Cursor, KConfigGen)
    Start = Cursor.Offset
    Initial = allocation_state(Cursor)
    Relation, AtomCount = ReadRelEntry(Config, Layouts, (2,))
    RequireArch(AtomCount, 2, "independent configured atom roster")
    RequireArch(EndGhosts(Config, Start), Relation.offset, "independent ghost boundary")

    Saved = ReadGhostRelationManagers(Cursor, KConfigGen, SketchPointCount=2)
    Independent = ArchiveCursor(
        Config,
        Relation.offset + ReadTag(Config, Relation.offset).size,
        Relation.Counter,
        Relation.Classes,
        Relation.Objects,
    )
    ReadEmptyRel(Independent)
    RequireArch(Cursor.Offset, Independent.Offset, "independently reached saved detail")
    RequireArch(allocation_state(Cursor), allocation_state(Independent), "relation map")
    ReadDetailStart(Independent)

    Writer = PartArchiveWriter(Initial)
    Fresh = WriteGhostRelationManagers(
        Writer,
        KConfigGen,
        GhostPartitionPopulated=True,
        AutoSolveOrder=True,
        SketchPointCount=2,
    )
    Span = Writer.build()
    RequireArch(Fresh, Saved, "fresh ghost and relation identities")
    RequireArch(Span, Config[Start : Cursor.Offset], "fresh ghost and relation bytes")
    RequireArch(
        Writer.Snapshot(), allocation_state(Cursor), "fresh relation allocation"
    )
    GhostSpan = Config[Start : Relation.offset]
    return {
        "offset": Start,
        "relation_offset": Relation.offset,
        "detail_offset": Cursor.Offset,
        "detail_header_end": Independent.Offset,
        "archived_bytes": len(Span),
        "ghost_bytes": len(GhostSpan),
        "latest_ghost_id": Fresh.GhostId,
        "relation_occurrence": Fresh.RelationObject,
        "ghost_sha256": sha256(GhostSpan).hexdigest(),
        "manager_sha256": sha256(Span).hexdigest(),
    }


# use new compact slots and reject contradictory counts and record fields
def CheckFresh() -> dict[str, object]:
    Writer = PartArchiveWriter()
    Writer.BeginObject(KModelDataClass, 1)
    Initial = Writer.Snapshot()
    Writer = PartArchiveWriter(Initial)
    Fresh = WriteGhostRelationManagers(
        Writer,
        KConfigGen,
        GhostPartitionPopulated=True,
        AutoSolveOrder=True,
        SketchPointCount=2,
    )
    Data = Writer.build()
    Cursor = Initial.Cursor(Data, 0)
    RequireArch(
        ReadGhostRelationManagers(Cursor, KConfigGen, SketchPointCount=2),
        Fresh,
        "fresh two-record readback",
    )
    RequireArch(
        (Cursor.Offset, Fresh.RelationObject),
        (len(Data), Initial.NextIndex + 1),
        "inline ghosts allocate no archive objects",
    )
    Refusals = 0
    for Count, Populated, AutoOrder in (
        (0, True, True),
        (3, True, True),
        (True, True, True),
        (2, False, True),
        (2, True, False),
    ):
        Refused = PartArchiveWriter(Initial)
        try:
            WriteGhostRelationManagers(
                Refused,
                KConfigGen,
                GhostPartitionPopulated=Populated,
                AutoSolveOrder=AutoOrder,
                SketchPointCount=Count,
            )
        except ArchiveError:
            RequireArch(
                (Refused.Snapshot(), Refused.build()),
                (Initial, b""),
                "write refusal before output",
            )
            Refusals += 1
        else:
            raise ArchiveError("accepted an unsupported ghost manager state")

    for Offset, Value in (
        (0, 10001),
        (4, 0x20000001),
        (4, 0x10000002),
        (8, 10001),
        (40, 10002),
        (44, 21),
        (60, 23),
        (64, 1),
    ):
        Altered = bytearray(Data)
        PackInto("<i", Altered, Offset, Value)
        try:
            ReadGhostRelationManagers(
                Initial.Cursor(bytes(Altered), 0), KConfigGen, SketchPointCount=2
            )
        except ArchiveError:
            Refusals += 1
        else:
            raise ArchiveError("accepted a conflicting ghost record")
    return {
        "relation_occurrence": Fresh.RelationObject,
        "manager_sha256": sha256(Data).hexdigest(),
        "refusals": Refusals,
    }


# the private archive list is accepted only through the original sealed discovery proof
def RunVerification() -> None:
    Parser = ArgumentParser(
        description="Replay the two-pad ghost and relation manager."
    )
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
        Case["variant"]: CheckManagers(
            ReadPadBytes(
                Args.run_directory, f"{Case['variant']}.SLDPRT", Case["archive_sha256"]
            )
        )
        for Case in Native["cases"]
    }
    Report = {
        "capture_source_revision": Native["capture_source_revision"],
        "native_report_sha256": Native["report_sha256"],
        "native_observations": Native["verified_native_observations"],
        "stock_controls": Native["stock_controls"],
        "cases": Cases,
        "fresh": CheckFresh(),
    }
    Payload = DumpJson(Report, sort_keys=True, separators=(",", ":"), allow_nan=False)
    sys.stdout.buffer.write((Payload + "\n").encode("utf-8"))


if __name__ == "__main__":
    RunVerification()
