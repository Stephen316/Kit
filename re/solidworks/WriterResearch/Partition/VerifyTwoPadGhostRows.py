# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from argparse import ArgumentParser
from dataclasses import dataclass as Dataclass
from hashlib import sha256
from json import dumps as DumpJson
from pathlib import Path
from struct import Struct, pack as Pack
import sys

# resolve the sdk and licensed audit from the source checkout
KRepository = Path(__file__).resolve().parents[4]

# the copied custody directory never supplies executable modules
sys.path[:0] = [
    str(KRepository / "src"),
    str(KRepository / "re/automation"),
    str(KRepository / "re/automation/TwoPad"),
    str(KRepository / "re/solidworks/WriterResearch"),
    str(KRepository / "re/solidworks/WriterResearch/TwoPadAtoms"),
]

from ConfigGhostRelation import ReadGhostRelationManagers
from ConfigRoot import OpenConfigRoot
from PadReceipts import ReadPadBytes
from Partition.AttrRows import (
    EncodeGhostInstance,
    EncodeGhostName,
    GhostAttributeSlots,
    KGhostName,
)
from Partition.PointRows import (
    EncodeGhostRows,
    GhostAllocation,
    GhostRowMarks,
    KPointSchema,
)
from VerifyDiscovery import AuditDiscovery
from WritePadAtoms import ReadPadAtoms
from convert.adapters.solidworks.Config.ModelEntry import ReadModelEntry
from convert.adapters.solidworks.Config.RootLayout import KConfigGen, LoadPartLayouts
from convert.adapters.solidworks.Container.Archive import ArchiveError
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Parasolid import DecodePartition
from convert.adapters.solidworks.Core.Partition.PartRecordBody import FindPartBodies
from convert.adapters.solidworks.Core.Partition.PartShellOwner import KShellRecord
from convert.Geometry.Parasolid import (
    KMissingParam,
    ParaHeaderData,
    ParaWriteError,
    ReadBrepResult,
    ScanPartRecords,
)
from interchange.geometry.Models.VectorSpace import SpaceVector

# the named configuration owns the side partition independent of the merged solid
KStreamName = "Contents/Config-0-GhostPartition"

# these layouts carry the references connecting ghost bodies and geometry rows
KNameRow = Struct(f">IH{len(KGhostName)}s")

# definition state precedes the name referenced by both instances
KDefinition = Struct(">i3Hi8BB18B2B")

# attached attributes expose the body and its integer value slot
KAttribute = Struct(">IHi8H")

# integer arrays hold the configured ghost identities in separate value rows
KInteger = Struct(">IHi")

# the point and vertex layouts use the same short references as the packaged scanner
KPointRow = Struct(">Hi4H3d")

# the isolated vertex ends with an explicit shell reference
KVertexRow = Struct(">Hi5HdH")

# the pinned body layout joins its attribute and all four topology heads
KBodyRow = Struct(">Hi9H2d3HBH2B10Hi4HiH")


# retain reached attribute and value positions with their independent class order
@Dataclass(frozen=True, slots=True)
class GhostOwner:
    AttributeOffset: int
    ValueOffset: int
    AttributeId: int
    AttributeNode: int
    GhostId: int
    FirstAttribute: bool
    FirstValue: bool


# exact record marks are checked against first placement for their own class
def CheckSpan(Data: bytes, Start: int, Kind: int, Marked: bool, Encoded: bytes) -> str:
    Offset = Start - 2 - int(Marked)
    RequireArch(Data[Offset : Offset + 2], Pack(">H", Kind), "ghost row class boundary")
    RequireArch(
        Data[Offset : Offset + len(Encoded)], Encoded, "generated ghost row bytes"
    )
    return sha256(Encoded).hexdigest()


# one physical name must be shared by the exact owner definition row
def ReadDefinition(Data: bytes) -> tuple[int, int]:
    Name = KGhostName.encode("ascii")
    Rows = [
        (Offset, Slot)
        for Offset in FindPartBodies(Data, 79, KNameRow.size, HasMarker=True)
        for Size, Slot, Value in (KNameRow.unpack_from(Data, Offset),)
        if Size == len(Name) and Value == Name and Slot > 1
    ]
    RequireArch(len(Rows), 1, "unique ghost reference attribute name")
    Offset, NameId = Rows[0]
    NameStart = Offset - 3
    RequireArch(NameStart >= KDefinition.size, True, "preceding ghost definition")
    Count, DefId, Empty, Alias, Domain, *Fields = KDefinition.unpack_from(
        Data, NameStart - KDefinition.size
    )
    RequireArch(
        (Count, Empty, Alias, Domain), (2, 1, NameId, 9000), "shared ghost definition"
    )
    RequireArch(DefId > 1 and Fields[4:7] == [3, 6, 0], True, "ghost definition fields")
    CheckSpan(Data, Offset, 79, True, EncodeGhostName(NameId - 1))
    return NameId, DefId


# the isolated vertex and void region must reach exactly one ghost body
def ReadGhostShell(Data: bytes, Shell: int, Vertex: int) -> tuple[int, int]:
    Shells = [
        (Body, Region)
        for Offset in FindPartBodies(Data, 13, KShellRecord.size, HasMarker=True)
        for Id, Node, Empty, Body, Next, Face, Edge, End, Region, Comp in (
            KShellRecord.unpack_from(Data, Offset),
        )
        if (Id, End) == (Shell, Vertex)
        and Node > 0
        and min(Body, Region) > 1
        and (Empty, Next, Face, Edge, Comp) == (1,) * 5
    ]
    RequireArch(len(Shells), 1, "unique faceless shell joins the bound body and vertex")
    return Shells[0]


# the body must point back to its attribute and the reached topology records
def CheckBody(
    Data: bytes, Shell: int, Vertex: int, Point: int, Owner: int, Region: int, Attr: int
) -> None:
    Counter = Pack(">H", Owner)
    Bodies = [
        Values
        for Offset in range(len(Data) - KBodyRow.size + 1)
        if Data.startswith(Counter, Offset)
        for Values in (KBodyRow.unpack_from(Data, Offset),)
        if (Values[2], Values[20], Values[24], Values[27], Values[29])
        == (Attr, Shell, Point, Region, Vertex)
        and Values[1] > 0
        and Values[18:20] == (2, 1)
    ]
    RequireArch(
        len(Bodies), 1, "body reaches the exact attribute and faceless geometry"
    )


# attribute and integer classes are independently ordered before matching body ownership
def FindGhostIds(
    Data: bytes, Definition: int, Keys: tuple[int, int]
) -> dict[int, GhostOwner]:
    Attributes = [
        (Offset, Attr, Node, Body, Value)
        for Offset in FindPartBodies(Data, 81, KAttribute.size, HasMarker=True)
        for Count, Attr, Node, Def, Body, *Refs in (
            KAttribute.unpack_from(Data, Offset),
        )
        for Value in (Refs[-1],)
        if Count == 2
        and Def == Definition
        and min(Attr, Node, Body, Value) > 1
        and Refs[:-1] == [1] * 5
    ]
    Integers = [
        (Offset, Slot, GhostId)
        for Offset in FindPartBodies(Data, 82, KInteger.size, HasMarker=True)
        for Count, Slot, GhostId in (KInteger.unpack_from(Data, Offset),)
        if Count == 1 and GhostId in Keys and Slot > 1
    ]
    RequireArch(len(Attributes), 2, "two ghost body attributes")
    RequireArch({Row[2] for Row in Integers}, set(Keys), "configured ghost identities")
    RequireArch(len(Integers), 2, "two unique ghost values")
    RequireArch(
        {Row[4] for Row in Attributes},
        {Row[1] for Row in Integers},
        "attribute value roster",
    )
    Result = {}
    for Position, (AttrOffset, Attr, Node, Body, Value) in enumerate(Attributes):
        [(ValuePosition, ValueOffset, GhostId)] = [
            (Index, Offset, Key)
            for Index, (Offset, Slot, Key) in enumerate(Integers)
            if Slot == Value
        ]
        RequireArch(Body not in Result, True, "distinct physical ghost body owners")
        Result[Body] = GhostOwner(
            AttrOffset,
            ValueOffset,
            Attr,
            Node,
            GhostId,
            Position == 0,
            ValuePosition == 0,
        )
    return Result


# verified configured ghosts establish the whole expected physical owner set
def ReadConfigIds(Archive: SldprtArchive) -> tuple[int, int]:
    Config = Archive.require("Contents/Config-0")
    _, Split = OpenConfigRoot(Config)
    Model, _ = ReadModelEntry(Config, LoadPartLayouts())
    Cursor = ArchiveCursor(
        Config, Split + 4, Model.Counter, Model.Classes, Model.Objects
    )
    ReadPadAtoms(Cursor, KConfigGen)
    Manager = ReadGhostRelationManagers(Cursor, KConfigGen, SketchPointCount=2)
    return Manager.GhostId - 1, Manager.GhostId


# the codec must reconstruct every reached row with first marks in typed occurrence order
def CheckGhosts(Streams: SldprtArchive) -> dict[str, object]:
    Source = Streams.require(KStreamName)
    (Payload,) = DecodePartition(Source, KStreamName)
    Header = ParaHeaderData(Payload.data)
    if Header is None or Header.schema != KPointSchema or Payload.kind != "partition":
        raise ParaWriteError("unsupported two pad ghost partition")
    Data = Payload.data[Header.body_offset :]
    Tables = ScanPartRecords(Data)
    if Tables is None:
        raise ParaWriteError("unreadable two pad ghost rows")
    RequireArch(
        (len(Tables.points), len(Tables.vertex_uses)),
        (2, 2),
        "two point and vertex records",
    )
    RequireArch(len(Tables.edge_uses), 0, "ghost partition has no physical edges")
    RequireArch(
        ReadBrepResult(Payload.data),
        (None, "partition contains no decoded faces"),
        "faceless ghost geometry",
    )
    Keys = ReadConfigIds(Streams)
    Name, Definition = ReadDefinition(Data)
    Owners = FindGhostIds(Data, Definition, Keys)
    Rows = {}
    PointStart = min(Value.offset for Value in Tables.points.values())
    VertexStart = min(Value.offset for Value in Tables.vertex_uses.values())
    for Point in Tables.points.values():
        Vertex = Tables.vertex_uses[Point.references[1]]
        RequireArch(Point.references, (1, Vertex.attribute, 1, 1), "owned ghost point")
        RequireArch(
            Vertex.references, (1, 1, 1, 1, Point.attribute), "reciprocal ghost vertex"
        )
        PointMark, VertexMark = Point.offset == PointStart, Vertex.offset == VertexStart
        PointIn = Point.offset + 2 + int(PointMark)
        VertexIn = Vertex.offset + 2 + int(VertexMark)
        PointId, PointNode, *Coordinates = KPointRow.unpack_from(Data, PointIn)
        VertexId, VertexNode, *BodyLinks, Shell = KVertexRow.unpack_from(Data, VertexIn)
        RequireArch(
            (PointId, VertexId),
            (Point.attribute, Vertex.attribute),
            "matches typed scanner slots",
        )
        RequireArch(
            tuple(BodyLinks[:5]), Vertex.references, "matches typed vertex references"
        )
        Owner, Region = ReadGhostShell(Data, Shell, VertexId)
        RequireArch(
            Owner in Owners, True, "one shell reaches a configured ghost attribute body"
        )
        Binding = Owners[Owner]
        GhostId = Binding.GhostId
        CheckBody(Data, Shell, VertexId, PointId, Owner, Region, Binding.AttributeId)
        _, ValueSlot, _ = KInteger.unpack_from(Data, Binding.ValueOffset)
        X, Y, Z = Coordinates[-3:]
        RequireArch(
            Point.point, SpaceVector(X, Y, Z), "defined physical point coordinates"
        )
        Marks = GhostRowMarks(PointMark, VertexMark, Binding.FirstValue)
        Slots = GhostAllocation(
            Shell - 1, PointId - 1, VertexId - 1, ValueSlot - 1, PointNode, VertexNode
        )
        AttrSlots = GhostAttributeSlots(
            Name - 1,
            Binding.AttributeId - 1,
            Definition - 1,
            Owner - 1,
            ValueSlot - 1,
            Binding.AttributeNode,
        )
        Fresh = EncodeGhostRows(
            SpaceVector(1000 * X, 1000 * Y, 1000 * Z),
            Slots,
            GhostId,
            Schema=Header.schema,
            Marks=Marks,
        )
        AttrBytes = EncodeGhostInstance(
            AttrSlots, Schema=Header.schema, Marked=Binding.FirstAttribute
        )
        RequireArch(
            GhostId not in Rows,
            True,
            "each configured ghost reaches one physical point",
        )
        Rows[GhostId] = {
            "body": Owner,
            "shell": Shell,
            "physical_point_m": [X, Y, Z],
            "markers": [*Marks, Binding.FirstAttribute],
            "row_sha256": [
                CheckSpan(Data, PointIn, 29, PointMark, Fresh.point),
                CheckSpan(Data, VertexIn, 18, VertexMark, Fresh.vertex),
                CheckSpan(
                    Data, Binding.ValueOffset, 82, Binding.FirstValue, Fresh.integer
                ),
                CheckSpan(
                    Data, Binding.AttributeOffset, 81, Binding.FirstAttribute, AttrBytes
                ),
            ],
        }
    RequireArch(set(Rows), set(Keys), "physical bodies cover the configured ghost IDs")
    return {"stream_sha256": sha256(Source).hexdigest(), "physical_ghosts": Rows}


# new coordinates and transport slots prove the rows use caller ownership
def VerifyFreshRows() -> dict[str, object]:
    Slots = GhostAllocation(21, 25, 27, 37, 19, 14)
    Point = SpaceVector(125.0, -250.0, 500.0)
    Marks = GhostRowMarks(False, True, False)
    Rows = EncodeGhostRows(Point, Slots, 10123, Schema=KPointSchema, Marks=Marks)
    AttrSlots = GhostAttributeSlots(32, 38, 31, 30, 37, 19)
    Instance = EncodeGhostInstance(AttrSlots, Schema=KPointSchema, Marked=False)
    RequireArch(
        KPointRow.unpack_from(Rows.point, 2),
        (26, 19, 1, 28, 1, 1, 0.125, -0.25, 0.5),
        "fresh positioned point and vertex link",
    )
    RequireArch(
        KVertexRow.unpack_from(Rows.vertex, 3),
        (28, 14, 1, 1, 1, 1, 26, KMissingParam, 22),
        "fresh reciprocal vertex and shell link",
    )
    RequireArch(
        KInteger.unpack_from(Rows.integer, 2), (1, 38, 10123), "fresh owned ghost value"
    )
    RequireArch(
        KAttribute.unpack_from(Instance, 2),
        (2, 39, 19, 32, 31, 1, 1, 1, 1, 1, 38),
        "fresh shared definition and owned value",
    )

    Refused = 0
    for BadSlots, GhostId, Schema in (
        (GhostAllocation(21, 21, 27, 37, 19, 14), 10123, KPointSchema),
        (GhostAllocation(21, 25, 27, 37, 19, 19), 10123, KPointSchema),
        (Slots, 10000, KPointSchema),
        (Slots, 10123, "other schema"),
    ):
        try:
            EncodeGhostRows(Point, BadSlots, GhostId, Schema=Schema, Marks=Marks)
        except ParaWriteError:
            Refused += 1
        else:
            raise ParaWriteError("an invalid ghost row allocation encoded")
    try:
        CheckSpan(Rows.point, 2, 29, True, Rows.point)
    except ArchiveError:
        Refused += 1
    else:
        raise ParaWriteError("an unmarked row passed as the first class occurrence")
    return {
        "sha256": sha256(b"".join((*Rows, Instance))).hexdigest(),
        "refusals": Refused,
    }


# seal a deterministic report after the independent audit of all source files
def RunVerification() -> None:
    Parser = ArgumentParser(description="Reproduce the two pad side partition rows.")
    Parser.add_argument("--run-directory", required=True, type=Path)
    Parser.add_argument("--source-revision", required=True)
    Parser.add_argument("--report-sha256", required=True)
    Parser.add_argument("--authoring-sha256", required=True)
    Parser.add_argument("--reopen-sha256", required=True)
    Args = Parser.parse_args()
    Audit = AuditDiscovery(
        Args.run_directory,
        KRepository,
        Args.source_revision,
        Args.report_sha256,
        Args.authoring_sha256,
        Args.reopen_sha256,
        True,
    )
    Cases = {}
    for Case in Audit["cases"]:
        Variant, Digest = Case["variant"], Case["archive_sha256"]
        Raw = ReadPadBytes(Args.run_directory, f"{Variant}.SLDPRT", Digest)
        Cases[Variant] = CheckGhosts(SldprtArchive.from_bytes(Raw))
    Report = {
        "native_report_sha256": Audit["report_sha256"],
        "native_observations": Audit["verified_native_observations"],
        "healthy_stock_controls": Audit["stock_controls"],
        "cases": Cases,
        "fresh": VerifyFreshRows(),
    }
    Result = DumpJson(Report, sort_keys=True, separators=(",", ":"), allow_nan=False)
    sys.stdout.buffer.write((Result + "\n").encode("utf-8"))


if __name__ == "__main__":
    RunVerification()
