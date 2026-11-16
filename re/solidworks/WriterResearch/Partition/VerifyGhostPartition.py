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
from struct import Struct, pack as Pack
import sys

# only versioned source supplies the codec and independent evidence reader
KRepository = Path(__file__).resolve().parents[4]

# private captures remain data outside the module search path
sys.path[:0] = [
    str(KRepository / "src"),
    str(KRepository / "re/automation"),
    str(KRepository / "re/automation/TwoPad"),
    str(KRepository / "re/solidworks/WriterResearch"),
]

from PadReceipts import ReadPadBytes
from Partition.GhostBodyRows import GhostBodyLinks, GhostBodySpec
from Partition.PointRows import KPointSchema
from Partition.VerifyTwoPadGhostBodies import ReadGhostBody, ReadWorld
from Partition.VerifyTwoPadGhostRows import (
    FindGhostIds,
    KInteger,
    KPointRow,
    KStreamName,
    KVertexRow,
    ReadConfigIds,
    ReadDefinition,
)
from Partition.VerifyTwoPadGhostTopo import GetTopology
from Partition.WorldRow import GhostWorld
from Partition.WriteGhostPartition import (
    EncodeGhostPartition,
    GhostNodeIds,
    GhostPartitionBody,
)
from VerifyDiscovery import AuditDiscovery
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Parasolid import DecodePartition
from convert.Geometry.Parasolid import ParaHeaderData, ParaWriteError, ScanPartRecords
from interchange.geometry.Models.VectorSpace import SpaceVector

# a body list files its attribute array at both reached link positions
KListRow = Struct(">HiBB3H3i2H")

# the pointer array contains one owned attribute in this configured scope
KArrayRow = Struct(">IHiiH20H")


# require the list and its independently reached array to share the body attribute
def ReadArraySlot(Data: bytes, Links: GhostBodyLinks) -> int:
    ListSlot = Links.attribute_list + 1
    Prefix = Pack(">H", ListSlot)
    Lists = [
        Fields[-1]
        for Offset in range(len(Data) - KListRow.size + 1)
        if Data.startswith(Prefix, Offset)
        for Fields in (KListRow.unpack_from(Data, Offset),)
        if Fields[:10] == (ListSlot, 0, 4, 1, Links.body + 1, 1, 1, 1, 20, 1)
        and Fields[-2] == Fields[-1] > 1
    ]
    RequireArch(len(Lists), 1, "one body list owns the reached array")
    Array = Lists[0]
    Signature = Pack(">IH", 20, Array)
    Matches = [
        Offset
        for Offset in range(len(Data) - KArrayRow.size + 1)
        if Data.startswith(Signature, Offset)
        and KArrayRow.unpack_from(Data, Offset)
        == (20, Array, 1, 0, 1, Links.attribute + 1, *([1] * 19))
    ]
    RequireArch(len(Matches), 1, "one occupied pointer belongs to the ghost body")
    return Array - 1


# reach all caller inputs through configured ghost identities and native graph records
def ReadNativeGraph(
    Data: bytes, Keys: tuple[int, int]
) -> tuple[GhostWorld, int, tuple[GhostPartitionBody, GhostPartitionBody]]:
    Tables = ScanPartRecords(Data)
    if Tables is None:
        raise ParaWriteError("unreadable ghost partition body")
    World, _, _ = ReadWorld(Data)
    Name, Definition = ReadDefinition(Data)
    RequireArch(Definition, World.definition + 1, "world owns the ghost definition")
    Owners = FindGhostIds(Data, Definition, Keys)
    PointOrder = sorted(
        (Point.offset, Slot)
        for Slot, Point in Tables.points.items()
        if Point.references[1] in Tables.vertex_uses
        and Tables.vertex_uses[Point.references[1]].references == (1, 1, 1, 1, Slot)
    )
    RequireArch(
        (len(PointOrder), len(Tables.vertex_uses)), (2, 2), "two isolated point bodies"
    )
    Bodies = []
    for Position, (_, PointId) in enumerate(PointOrder):
        First = Position == 0
        Body, _, GhostId = ReadGhostBody(Data, Tables, PointId, First, World, Owners)
        Topology, _ = GetTopology(Data, Tables, PointId, First)
        Point = Tables.points[PointId]
        Vertex = Tables.vertex_uses[Topology.vertex + 1]
        if Point.point is None:
            raise ParaWriteError("ghost point has no physical coordinates")
        InPoint = Point.point
        Binding = Owners[Body.links.body + 1]
        PointNode = KPointRow.unpack_from(Data, Point.offset + 2 + int(First))[1]
        VertexNode = KVertexRow.unpack_from(Data, Vertex.offset + 2 + int(First))[1]
        ValueSlot = KInteger.unpack_from(Data, Binding.ValueOffset)[1] - 1
        Bodies.append(
            GhostPartitionBody(
                Body,
                SpaceVector(InPoint.x, InPoint.y, InPoint.z),
                GhostNodeIds(
                    Binding.AttributeNode,
                    Topology.shell_node,
                    PointNode,
                    Topology.region_node,
                    VertexNode,
                ),
                GhostId,
                ValueSlot,
                ReadArraySlot(Data, Body.links),
            )
        )
    Leading, Following = Bodies
    return World, Name - 1, (Leading, Following)


# both the transport bytes and expanded partition must match the sealed source
def CheckArchive(Archive: SldprtArchive) -> dict[str, object]:
    Original = Archive.require(KStreamName)
    (Payload,) = DecodePartition(Original, KStreamName)
    Header = ParaHeaderData(Payload.data)
    if Header is None or Header.schema != KPointSchema or Payload.kind != "partition":
        raise ParaWriteError("unsupported ghost partition frame")
    Data = Payload.data[Header.body_offset :]
    Source = ReadNativeGraph(Data, ReadConfigIds(Archive))
    Fresh = EncodeGhostPartition(*Source)
    RequireArch(Fresh, Original, "complete two point partition transport")
    (Output,) = DecodePartition(Fresh, KStreamName)
    RequireArch(Output.data, Payload.data, "complete expanded partition")
    Reached = ReadNativeGraph(Output.data[Header.body_offset :], ReadConfigIds(Archive))
    RequireArch(Reached, Source, "readback of both regenerated ghost body graphs")
    return {
        "compressed_sha256": sha256(Fresh).hexdigest(),
        "expanded_sha256": sha256(Output.data).hexdigest(),
        "body_rows_sha256": sha256(Data).hexdigest(),
        "compressed_bytes": len(Fresh),
        "expanded_bytes": len(Output.data),
    }


# distinct point coordinates and allocations distinguish the writer from source replay
def CheckFresh() -> dict[str, object]:
    World = GhostWorld(23, 31, 28, 17, 16)
    Leading = GhostPartitionBody(
        GhostBodySpec(
            GhostBodyLinks(31, 37, 42, 43, 45, 47, 48), 19, 425.0, 0.00000002
        ),
        SpaceVector(125.0, -250.0, 500.0),
        GhostNodeIds(19, 13, 17, 15, 9),
        10002,
        49,
        50,
    )
    Following = GhostPartitionBody(
        GhostBodySpec(
            GhostBodyLinks(61, 67, 72, 73, 75, 77, 78), 21, 550.0, 0.00000003
        ),
        SpaceVector(-1000.0, 250.0, 0.0),
        GhostNodeIds(21, 16, 18, 17, 11),
        10001,
        79,
        80,
    )
    Input = (World, 52, (Leading, Following))
    Fresh = EncodeGhostPartition(*Input)
    (Payload,) = DecodePartition(Fresh)
    Header = ParaHeaderData(Payload.data)
    if Header is None:
        raise ParaWriteError("missing fresh ghost header")
    RequireArch(
        ReadNativeGraph(Payload.data[Header.body_offset :], (10001, 10002)),
        Input,
        "fresh two point physical graph",
    )

    Refusals = 0
    for Bodies in (
        (Following, Leading),
        (Leading, Following._replace(array_slot=Leading.array_slot)),
        (Leading, Following._replace(point=SpaceVector(float("inf"), 0.0, 0.0))),
        (Leading._replace(nodes=Leading.nodes._replace(region=19)), Following),
        (Leading._replace(body=Leading.body._replace(highest_node=20)), Following),
    ):
        try:
            EncodeGhostPartition(World, 52, Bodies)
        except ParaWriteError:
            Refusals += 1
        else:
            raise ParaWriteError("contradictory ghost graph encoded")
    return {"compressed_sha256": sha256(Fresh).hexdigest(), "refusals": Refusals}


# seal the recreated partition only after auditing the original licensed capture
def RunVerification() -> None:
    Parser = ArgumentParser(
        description="Recreate the complete sealed two point side partition."
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
        "native_observations": Native["verified_native_observations"],
        "stock_controls": Native["stock_controls"],
    }
    Payload = DumpJson(Report, sort_keys=True, separators=(",", ":"), allow_nan=False)
    sys.stdout.buffer.write((Payload + "\n").encode("utf-8"))


if __name__ == "__main__":
    RunVerification()
