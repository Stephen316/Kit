# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from argparse import ArgumentParser
from dataclasses import replace as Replace
from hashlib import sha256
from json import dumps as DumpJson
from pathlib import Path
from struct import Struct, pack as Pack
import sys

# verifier modules come from the checkout rather than private custody
KRepository = Path(__file__).resolve().parents[4]

# share the existing archive and independent licensed proof helpers
sys.path[:0] = [
    str(KRepository / "src"),
    str(KRepository / "re/automation"),
    str(KRepository / "re/automation/TwoPad"),
    str(KRepository / "re/solidworks/WriterResearch"),
]

from PadReceipts import ReadPadBytes
from Partition.GhostBodyRows import EncodeTwoGhostBodies, GhostBodyLinks, GhostBodySpec
from Partition.PointRows import KPointSchema
from Partition.VerifyTwoPadGhostRows import (
    FindGhostIds,
    GhostOwner,
    KBodyRow,
    KPointRow,
    KStreamName,
    KVertexRow,
    ReadConfigIds,
    ReadDefinition,
)
from Partition.VerifyTwoPadGhostTopo import GetTopology
from Partition.WorldRow import GhostWorld, GhostWorldSchema
from VerifyDiscovery import AuditDiscovery
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Parasolid import DecodePartition
from convert.Geometry.Parasolid import (
    ParaHeaderData,
    ParaWriteError,
    RecordTables,
    ScanPartRecords,
)

# this interpreted world row exposes its leading body and its own allocator counters
KWorldFields = Struct(">11HB2H3i3H")


# the world leads the exact shared definition and ordered first body
def ReadWorld(Data: bytes) -> tuple[GhostWorld, int, int]:
    Class = bytes(GhostWorldSchema())
    Start = Data.find(Class)
    RequireArch((Start, Data.count(Class)), (6, 1), "unique declared ghost world")
    BodyStart = Start + len(Class)
    Records = KWorldFields.unpack_from(Data, BodyStart)
    State = GhostWorld(
        Records[0] - 1, Records[3] - 1, Records[12] - 1, Records[14], Records[15]
    )
    return State, Start, BodyStart + KWorldFields.size


# typed point and shell owners discover each body without using its saved order links
def ReadGhostBody(
    Data: bytes,
    Tables: RecordTables,
    PointId: int,
    First: bool,
    World: GhostWorld,
    Owners: dict[int, GhostOwner],
) -> tuple[GhostBodySpec, int, int]:
    Topology, _ = GetTopology(Data, Tables, PointId, First)
    Point = Tables.points[PointId]
    Vertex = Tables.vertex_uses[Topology.vertex + 1]
    Owner = Topology.body + 1
    Binding = Owners[Owner]
    PointNode = KPointRow.unpack_from(Data, Point.offset + 2 + int(First))[1]
    VertexNode = KVertexRow.unpack_from(Data, Vertex.offset + 2 + int(First))[1]
    NodeLimit = max(
        Binding.AttributeNode,
        PointNode,
        VertexNode,
        Topology.shell_node,
        Topology.region_node,
    )

    # the body row must join its existing attribute and all four topology heads
    Prefix = Pack(">H", Owner)
    Reached = [
        (Offset, Fields)
        for Offset in range(len(Data) - KBodyRow.size + 1)
        if Data.startswith(Prefix, Offset)
        for Fields in (KBodyRow.unpack_from(Data, Offset),)
        if (
            Fields[1],
            Fields[2],
            Fields[17],
            Fields[20],
            Fields[24],
            Fields[27],
            Fields[29],
        )
        == (
            NodeLimit,
            Binding.AttributeId,
            World.world + 1,
            Topology.shell + 1,
            PointId,
            Topology.region + 1,
            Vertex.attribute,
        )
        and Fields[16:20] == (1, World.world + 1, 2, 1)
    ]
    RequireArch(len(Reached), 1, "unique body row owns the same ghost geometry")
    Offset, Values = Reached[0]
    Links = GhostBodyLinks(
        Topology.body,
        Binding.AttributeId - 1,
        Values[3] - 1,
        Topology.shell,
        PointId - 1,
        Topology.region,
        Topology.vertex,
    )
    return (
        GhostBodySpec(Links, NodeLimit, Values[11], Values[12]),
        Offset,
        Binding.GhostId,
    )


# reconstruct the world and reciprocal body roster from independently reached owners
def CheckArchive(Archive: SldprtArchive) -> dict[str, object]:
    Stream = Archive.require(KStreamName)
    (Payload,) = DecodePartition(Stream, KStreamName)
    Header = ParaHeaderData(Payload.data)
    if Header is None or Payload.kind != "partition" or Header.schema != KPointSchema:
        raise ParaWriteError("unsupported ghost body partition scope")
    Data = Payload.data[Header.body_offset :]
    Tables = ScanPartRecords(Data)
    if Tables is None:
        raise ParaWriteError("unreadable ghost body table")
    World, Start, End = ReadWorld(Data)
    _, Definition = ReadDefinition(Data)
    RequireArch(
        Definition, World.definition + 1, "world owns the shared ghost definition"
    )
    Keys = ReadConfigIds(Archive)
    Owners = FindGhostIds(Data, Definition, Keys)
    PointOrder = sorted((Value.offset, Id) for Id, Value in Tables.points.items())
    RequireArch(
        (len(PointOrder), len(Tables.vertex_uses)), (2, 2), "two isolated ghost bodies"
    )
    First, FirstOffset, FirstKey = ReadGhostBody(
        Data, Tables, PointOrder[0][1], True, World, Owners
    )
    Second, SecondOffset, SecondKey = ReadGhostBody(
        Data, Tables, PointOrder[1][1], False, World, Owners
    )
    RequireArch(
        {FirstKey, SecondKey}, set(Keys), "only the configured ghost owners occur"
    )
    Fresh = EncodeTwoGhostBodies(World, (First, Second), Schema=Header.schema)
    RequireArch(
        tuple(Fresh),
        (
            Data[Start:End],
            Data[FirstOffset : FirstOffset + KBodyRow.size],
            Data[SecondOffset : SecondOffset + KBodyRow.size],
        ),
        "generated world and both body rows",
    )
    return {
        "stream_sha256": sha256(Stream).hexdigest(),
        "rows_sha256": sha256(b"".join(Fresh)).hexdigest(),
        "offsets": [Start, FirstOffset, SecondOffset],
        "size_bytes": list(map(len, Fresh)),
        "ghost_ids": [FirstKey, SecondKey],
        "body_slots": [First.links.body + 1, Second.links.body + 1],
        "model_resolution": [First.model_resolution, Second.model_resolution],
        "point_tolerance": [First.point_tolerance, Second.point_tolerance],
    }


# new slots and resolution inputs must round trip through the independent layouts
def CheckFresh() -> dict[str, object]:
    World = GhostWorld(23, 31, 28, 17, 16)
    First = GhostBodySpec(
        GhostBodyLinks(31, 37, 42, 43, 45, 47, 48), 13, 425.0, 0.00000002
    )
    Second = GhostBodySpec(
        GhostBodyLinks(36, 38, 51, 52, 54, 55, 56), 19, 550.0, 0.00000003
    )
    Fresh = EncodeTwoGhostBodies(World, (First, Second), Schema=KPointSchema)
    ReadbackWorld = KWorldFields.unpack_from(Fresh.world, len(GhostWorldSchema()))
    RequireArch(
        (ReadbackWorld[0], ReadbackWorld[3], ReadbackWorld[12], ReadbackWorld[14:16]),
        (24, 32, 29, (17, 16)),
        "fresh world and allocator counters",
    )
    A = KBodyRow.unpack(Fresh.first_body)
    B = KBodyRow.unpack(Fresh.second_body)
    RequireArch(
        (A[0], A[14:16], B[0], B[14:16]),
        (32, (37, 1), 37, (1, 32)),
        "fresh roster links are reciprocal",
    )
    RequireArch(
        (A[11:13], B[11:13]),
        ((425.0, 0.00000002), (550.0, 0.00000003)),
        "fresh physical resolution inputs",
    )

    Refusals = 0
    for Source, Bodies, Schema in (
        (Replace(World, body=36), (First, Second), KPointSchema),
        (World, (First, First), KPointSchema),
        (
            World,
            (First, Second._replace(links=Second.links._replace(vertex=48))),
            KPointSchema,
        ),
        (World, (First, Second._replace(highest_node=0)), KPointSchema),
        (World, (First._replace(model_resolution=float("nan")), Second), KPointSchema),
        (World, (First, Second), "other schema"),
    ):
        try:
            EncodeTwoGhostBodies(Source, Bodies, Schema=Schema)
        except ParaWriteError:
            Refusals += 1
        else:
            raise ParaWriteError("contradictory body allocation encoded")
    return {"sha256": sha256(b"".join(Fresh)).hexdigest(), "refusals": Refusals}


# the sealed native receipt establishes every source before any record comparison
def RunVerification() -> None:
    Parser = ArgumentParser(
        description="Reproduce the sealed two pad ghost world and body rows."
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
        "native_report_sha256": Native["report_sha256"],
        "native_observations": Native["verified_native_observations"],
        "stock_controls": Native["stock_controls"],
    }
    Payload = DumpJson(Report, sort_keys=True, separators=(",", ":"), allow_nan=False)
    sys.stdout.buffer.write((Payload + "\n").encode("utf-8"))


if __name__ == "__main__":
    RunVerification()
