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
from struct import Struct
import sys

# use only the pinned source tree for the private evidence verifier
KRepository = Path(__file__).resolve().parents[4]

# the public archive and native custody helpers stay read only
sys.path[:0] = [
    str(KRepository / "src"),
    str(KRepository / "re/automation"),
    str(KRepository / "re/automation/TwoPad"),
    str(KRepository / "re/solidworks/WriterResearch"),
]

from PadReceipts import ReadPadBytes
from Partition.PointRows import KPointSchema
from Partition.TopologyRows import EncodeGhostTopo, GhostTopoMarks, GhostTopology
from Partition.VerifyTwoPadGhostRows import (
    CheckBody,
    FindGhostIds,
    KPointRow,
    KStreamName,
    KVertexRow,
    ReadConfigIds,
    ReadDefinition,
    ReadGhostShell,
)
from VerifyDiscovery import AuditDiscovery
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Parasolid import DecodePartition
from convert.adapters.solidworks.Core.Partition.PartShellOwner import KShellRecord
from convert.Geometry.Parasolid import (
    ParaHeaderData,
    ParaWriteError,
    RecordTables,
    ScanPartRecords,
)

# the void region preserves explicit back references to its shell and body
KVoidRegion = Struct(">Hi6HcH")


# the selected shell and its region must complete both sides of the same point record
def GetTopology(
    Data: bytes,
    Tables: RecordTables,
    PointId: int,
    First: bool,
) -> tuple[GhostTopology, tuple[int, int, int]]:
    Point = Tables.points[PointId]
    Vertex = Tables.vertex_uses[Point.references[1]]
    RequireArch(
        (Point.references, Vertex.references),
        ((1, Vertex.attribute, 1, 1), (1, 1, 1, 1, PointId)),
        "reciprocal isolated point and vertex",
    )
    VertexIndex = Vertex.offset + 2 + int(First)
    Shell = KVertexRow.unpack_from(Data, VertexIndex)[-1]
    Owner, Region = ReadGhostShell(Data, Shell, Vertex.attribute)
    ShellBody = Point.offset - KShellRecord.size
    ShellStart = ShellBody - 2 - int(First)
    RegionStart = Point.offset + 2 + int(First) + KPointRow.size
    RegionBody = Vertex.offset - KVoidRegion.size
    Id, ShellNode, *_ = KShellRecord.unpack_from(Data, ShellBody)
    RequireArch(Id, Shell, "neighboring shell is the vertex owner")
    RegionId, RegionNode, Attr, Body, Sibling, Prev, ShellId, Extra, Sense, Frame = (
        KVoidRegion.unpack_from(Data, RegionBody)
    )
    RequireArch(
        (RegionId, Body, ShellId, Sense, Attr, Sibling, Prev, Extra, Frame),
        (Region, Owner, Shell, b"V", 1, 1, 1, 1, 1),
        "faceless region reaches its own body and shell",
    )
    Geometry = GhostTopology(
        Owner - 1, Shell - 1, Region - 1, Vertex.attribute - 1, ShellNode, RegionNode
    )
    return Geometry, (ShellStart, RegionStart, Vertex.offset)


# source spans close the topology and the configured ghost identity at the same offsets
def CheckArchive(Archive: SldprtArchive) -> dict[str, object]:
    Stream = Archive.require(KStreamName)
    (Payload,) = DecodePartition(Stream, KStreamName)
    Header = ParaHeaderData(Payload.data)
    if Payload.kind != "partition" or Header is None or Header.schema != KPointSchema:
        raise ParaWriteError("unsupported ghost partition topology scope")
    Data = Payload.data[Header.body_offset :]
    Tables = ScanPartRecords(Data)
    if Tables is None:
        raise ParaWriteError("unreadable ghost partition topology")
    Keys = ReadConfigIds(Archive)
    _, Definition = ReadDefinition(Data)
    Owners = FindGhostIds(Data, Definition, Keys)
    Points = sorted((Value.offset, Key) for Key, Value in Tables.points.items())
    RequireArch(
        (len(Points), len(Tables.vertex_uses)), (2, 2), "two isolated point pairs"
    )
    Rows = {}
    Whole = sha256()
    for Position, (_, PointId) in enumerate(Points):
        First = Position == 0
        Geometry, (ShellStart, RegionStart, End) = GetTopology(
            Data, Tables, PointId, First
        )
        Owner = Geometry.body + 1
        if Owner not in Owners:
            raise ParaWriteError("ghost shell body has no configured identifier")
        Binding = Owners[Owner]
        CheckBody(
            Data,
            Geometry.shell + 1,
            Geometry.vertex + 1,
            PointId,
            Owner,
            Geometry.region + 1,
            Binding.AttributeId,
        )
        Fresh = EncodeGhostTopo(
            Geometry, Schema=Header.schema, Marks=GhostTopoMarks(First, First)
        )
        ShellEnd = Tables.points[PointId].offset
        RequireArch(
            (Fresh.shell, Fresh.region),
            (Data[ShellStart:ShellEnd], Data[RegionStart:End]),
            "fresh closure matches both native records",
        )
        Whole.update(Fresh.shell + Fresh.region)
        RequireArch(
            Binding.GhostId not in Rows, True, "separate physical ghost topology owners"
        )
        Rows[Binding.GhostId] = {
            "body": Owner,
            "shell": Geometry.shell + 1,
            "region": Geometry.region + 1,
            "first_shell_mark": First,
            "first_region_definition": First,
            "size_bytes": [len(Fresh.shell), len(Fresh.region)],
        }
    RequireArch(
        set(Rows), set(Keys), "physical topology covers the configured ghost keys"
    )
    return {
        "stream_sha256": sha256(Stream).hexdigest(),
        "topology_sha256": Whole.hexdigest(),
        "ghosts": Rows,
    }


# changed graph slots exercise independent shell marker and region definition states
def CheckFresh() -> dict[str, object]:
    Slots = GhostTopology(91, 77, 89, 81, 17, 19)
    Rows = EncodeGhostTopo(
        Slots, Schema=KPointSchema, Marks=GhostTopoMarks(False, True)
    )
    RequireArch(
        KShellRecord.unpack_from(Rows.shell, 2),
        (78, 17, 1, 92, 1, 1, 1, 82, 90, 1),
        "fresh unmarked shell links",
    )
    RequireArch(
        KVoidRegion.unpack_from(Rows.region, len(Rows.region) - KVoidRegion.size),
        (90, 19, 1, 92, 1, 1, 78, 1, b"V", 1),
        "fresh defined region links",
    )
    Refused = 0
    for Invalid, Schema, Marks in (
        (GhostTopology(77, 77, 89, 81, 17, 19), KPointSchema, GhostTopoMarks()),
        (GhostTopology(91, 77, 89, 81, 17, 17), KPointSchema, GhostTopoMarks()),
        (Slots, "other schema", GhostTopoMarks()),
        (Slots, KPointSchema, GhostTopoMarks(region_definition=1)),
    ):
        try:
            EncodeGhostTopo(Invalid, Schema=Schema, Marks=Marks)
        except ParaWriteError:
            Refused += 1
        else:
            raise ParaWriteError("contradictory ghost topology allocation encoded")
    return {"sha256": sha256(Rows.shell + Rows.region).hexdigest(), "refusals": Refused}


# seal a full replay against the original discovery process evidence
def RunVerification() -> None:
    Parser = ArgumentParser(
        description="Reproduce both two pad ghost shell and region records."
    )
    Parser.add_argument("--run-directory", type=Path, required=True)
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
    Cases = {}
    for Case in Native["cases"]:
        Variant, Digest = Case["variant"], Case["archive_sha256"]
        Raw = ReadPadBytes(Args.run_directory, f"{Variant}.SLDPRT", Digest)
        Cases[Variant] = CheckArchive(SldprtArchive.from_bytes(Raw))
    Report = {
        "cases": Cases,
        "fresh": CheckFresh(),
        "licensed_observations": Native["verified_native_observations"],
        "stock_controls": Native["stock_controls"],
        "native_report_sha256": Native["report_sha256"],
    }
    Payload = DumpJson(Report, sort_keys=True, separators=(",", ":"), allow_nan=False)
    sys.stdout.buffer.write((Payload + "\n").encode("utf-8"))


if __name__ == "__main__":
    RunVerification()
