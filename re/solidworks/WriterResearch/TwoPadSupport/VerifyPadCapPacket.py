# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Check authored cap packets against five sealed projected support sheets."""

from argparse import ArgumentParser
from dataclasses import replace as Replace
from hashlib import sha256 as ShaValue
from json import dumps as DumpJson
from math import isclose as IsClose
from pathlib import Path as FilePath
from struct import pack as PackFields, unpack_from as UnpackFields
from sys import path as SearchPaths
from typing import TypedDict

# the standalone verifier uses first party readers and sealed receipts
KRepository = FilePath(__file__).resolve().parents[4]

# these source paths connect the standalone verifier to the existing owners
SearchPaths[:0] = [
    str(KRepository / Scope)
    for Scope in (
        "src",
        "re/automation",
        "re/automation/TwoPad",
        "re/solidworks/WriterResearch",
    )
]

from BossChoice import WriteChoiceCap
from BossOpen import KBossClass
from OriginSketch import KSketchClass
from PadReceipts import ReadPadBytes
from PartArchive import PartArchiveState, PartArchiveWriter
from PilotEvidence import pinned_record as ReadJsonPin
from RectangleTrim import KReferenceClass
from VerifyDiscovery import AuditDiscovery
from VerifyPadCap import KCapturePins, TakeCapState
from WritePadCapPacket import (
    CapPoint,
    EncodePadCapPacket,
    MakeCapRing,
    MakeCapSheet,
    PadCapBoss,
    PadCapSeat,
)
from convert.Geometry.ParaFraming import KWrapperMagic
from convert.adapters.solidworks.Config.OrdinaryMap import ReadEmptyMap
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import ArchiveError, KDefinitionKind
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Cmgr import KExtObjectClass
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Parasolid import (
    DecodeBrep,
    DecodePartition,
    EncodeBrep,
    EncodePartition,
    ParasolidPayload,
)
from convert.adapters.solidworks.Resolved.BossChooser import ReadCap, SavedCap
from convert.adapters.solidworks.Resolved.ContourChain import ReadChain
from convert.adapters.solidworks.Resolved.Cut.CutProfileBody import ReadKernelMut
from convert.adapters.solidworks.Resolved.FaceIdentity import SurfaceKey
from convert.adapters.solidworks.Resolved.OriginProfile import ReadOrigin
from convert.adapters.solidworks.Resolved.ProfileSketch import ReadProfileBody
from convert.adapters.solidworks.Resolved.ResolvedHead import OpenResolved
from convert.adapters.solidworks.Resolved.SystemPrefix import ReadSysPrefix
from convert.adapters.solidworks.Resolved.TwoPad.PadHistory import (
    KPadListCount,
    ReadBasePad,
    ReadPadSupport,
)
from convert.adapters.solidworks.Resolved.TwoPad.PadProfile import ReadPadProfMut
from convert.adapters.solidworks.Sketch.GeometryTypes import SketchGeometry, SketchLine
from interchange.brep.Curves.BrepCurves import LineCurve
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.geometry.Models.Transform import KTransformIdentity
from interchange.geometry.Models.VectorSpace import SpaceVector


# packet authority is tied to the explicitly passed saved file from the sealed receipt
class PadCapSave(TypedDict):
    file: str
    sha256: str


# an exact frame may consume only one compressed member and its explicit zero trailer
def ReadCapFrame(Packet: bytes, Initial: PartArchiveState) -> ParasolidPayload:
    Cursor = Initial.Cursor(Packet, 0)
    Span = ReadKernelMut(Cursor)
    RequireArch(Cursor.Offset, len(Packet), "exact embedded cap packet boundary")
    RequireArch(TakeCapState(Cursor), Initial, "embedded packet allocates no objects")
    Raw = Packet[Span["start"] : Span["end"]]
    RequireArch(
        37 < len(Raw) <= 8192 and Raw[0] == 0 and Raw[5:21] == KWrapperMagic,
        True,
        "one compact wrapped cap transmit",
    )
    (WrapperLength,) = UnpackFields("<I", Raw[1:5])
    RawSize, ZipSize = UnpackFields("<II", Raw[21:29])
    RequireArch(
        WrapperLength == len(Raw) - 5
        and 0 < RawSize <= 8192
        and 29 + ZipSize + 8 == len(Raw)
        and Raw[-8:] == bytes(8),
        True,
        "exact compressed cap length and trailer",
    )
    Payloads = DecodePartition(Raw)
    RequireArch(len(Payloads), 1, "exactly one embedded cap payload")
    (Payload,) = Payloads
    RequireArch(
        (Payload.wrapper_offset, Payload.compressed_offset, Payload.stored_size),
        (1, 29, len(Raw) - 1),
        "sole wrapper consumes the embedded cap region",
    )
    return Payload


# tolerant numeric comparison is limited to brep geometry in millimetres
def HasCapPoint(Vector: SpaceVector, Expected: CapPoint) -> bool:
    return all(
        IsClose(Value, Target, rel_tol=1e-12, abs_tol=1e-8)
        for Value, Target in zip((Vector.x, Vector.y, Vector.z), Expected, strict=True)
    )


# the typed graph must preserve the open body and its directed boundary
def CheckCapSheet(Model: BrepModel, Expected: tuple[CapPoint, ...]) -> None:
    RequireArch(Model.validate(), (), "valid typed support sheet")
    RequireArch(
        (
            len(Model.bodies),
            len(Model.regions),
            len(Model.shell_uses),
            len(Model.shells),
            len(Model.face_uses),
            len(Model.faces),
            len(Model.surfaces),
            len(Model.loops),
            len(Model.coedges),
            len(Model.edges),
            len(Model.vertices),
            len(Model.curves),
        ),
        (1,) * 8 + (4,) * 4,
        "one open four-sided support sheet",
    )
    (Body,) = Model.bodies
    (Region,) = Model.regions
    (ShellUse,) = Model.shell_uses
    (Shell,) = Model.shells
    (FaceUse,) = Model.face_uses
    (Face,) = Model.faces
    (Plane,) = Model.surfaces
    (Loop,) = Model.loops
    RequireArch(
        Body.region_ids == (Region.id,)
        and Body.transform == KTransformIdentity
        and not Body.wire_ids
        and not Body.vertex_ids
        and not Region.solid
        and Region.shell_use_ids == (ShellUse.id,)
        and ShellUse.shell_id == Shell.id
        and not ShellUse.reversed
        and not Shell.closed
        and Shell.face_use_ids == (FaceUse.id,)
        and FaceUse.face_id == Face.id
        and not FaceUse.reversed
        and Face.surface_id == Plane.id
        and not Face.same_sense
        and Face.loop_ids == (Loop.id,)
        and Loop.outer,
        True,
        "whole sheet owns one reversed plane and its sole outer ring",
    )
    if not isinstance(Plane, PlaneSurface):
        raise ArchiveError("embedded support does not contain a plane surface")
    RequireArch(
        HasCapPoint(Plane.origin, (0, 0, Expected[0][2]))
        and HasCapPoint(Plane.normal, (0, 0, -1))
        and HasCapPoint(Plane.reference_direction, (-1, 0, 0)),
        True,
        "embedded plane agrees with the reached world cap",
    )
    VertexById = {Value.id: Value.point for Value in Model.vertices}
    EdgeById = {Value.id: Value for Value in Model.edges}
    CoedgeById = {Value.id: Value for Value in Model.coedges}
    CurveById = {Value.id: Value for Value in Model.curves}
    Starts: list[SpaceVector] = []
    Ring: list[tuple[str, str]] = []
    for CoedgeId in Loop.coedge_ids:
        Coedge = CoedgeById[CoedgeId]
        Edge = EdgeById[Coedge.edge_id]
        RequireArch(
            isinstance(CurveById[Edge.curve_id], LineCurve),
            True,
            "straight cap carrier",
        )
        Pair = Edge.start_vertex_id, Edge.end_vertex_id
        Start, End = Pair[::-1] if Coedge.reversed else Pair
        Ring.append((Start, End))
        Starts.append(VertexById[Start])
    RequireArch(
        len({Start for Start, _ in Ring}) == 4
        and all(A[1] == B[0] for A, B in zip(Ring, Ring[1:] + Ring[:1], strict=True)),
        True,
        "directed cap ring has complete vertex incidence",
    )
    RequireArch(
        any(
            all(
                HasCapPoint(Point, Want)
                for Point, Want in zip(
                    Starts, Expected[At:] + Expected[:At], strict=True
                )
            )
            for At in range(len(Expected))
        ),
        True,
        "directed cap ring matches the lower-footprint cycle",
    )


# malformed framing and divergent cached geometry share an explicit offline boundary
def CheckPacket(
    BytesValue: bytes, Initial: PartArchiveState, Expected: tuple[CapPoint, ...]
) -> tuple[ParasolidPayload, BrepModel]:
    Payload = ReadCapFrame(BytesValue, Initial)
    Model = DecodeBrep(Payload.data)
    if Model is None:
        raise ArchiveError("embedded cap does not decode as a support sheet")
    CheckCapSheet(Model, Expected)
    return Payload, Model


# the archive replay independently reaches the earlier authored sketch and later support
def ReplayPadCapPacket(Directory: FilePath, Save: PadCapSave) -> dict[str, object]:
    Archive = SldprtArchive.from_bytes(
        ReadPadBytes(Directory, Save["file"], Save["sha256"])
    )
    Config = Archive.require("Contents/Config-0")
    Resolved = Archive.require("Contents/Config-0-ResolvedFeatures")
    Mapping, _ = ReadEmptyMap(Config, (2,))
    Lower = OpenResolved(Resolved, Mapping, KPadListCount)
    ReadSysPrefix(Lower)
    ReadOrigin(Lower, KConfigGen)
    Footprint = ReadProfileBody(Lower, KConfigGen)
    Upper = OpenResolved(Resolved, Mapping, KPadListCount)
    Owner, Close = ReadBasePad(Upper)
    Profile, _ = ReadPadProfMut(Upper)
    Support = ReadPadSupport(
        TakeCapState(Upper).Cursor(Resolved, Upper.Offset), Profile, Owner, Close
    )
    Cap = Owner["choosers"]["caps"][1]
    Face = Support["face"]
    Occurrence = Face["component"]["occurrence"]
    Seat = PadCapSeat(
        SurfaceKey(Occurrence["primary"]),
        tuple(SurfaceKey(Edge) for Edge in Occurrence["ordered_edges"]),
        Face["plane"],
    )
    RequireArch(
        Owner["profile_object"],
        Footprint.ObjectIndex,
        "reached lower profile belongs to boss",
    )
    RequireArch(Upper.ReadInts("<Ii"), (1, 1), "one earlier projected profile chain")
    ReadChain(Upper)
    Initial = TakeCapState(Upper)
    Start = Upper.Offset
    Span = ReadKernelMut(Upper)
    RequireArch(
        TakeCapState(Upper), Initial, "sealed packet leaves archive allocation intact"
    )
    Depth = Close["depth_display"]["dimension"]["metres"]
    Expected = MakeCapRing(Footprint.Geometry, Depth)
    Saved = Resolved[Start : Span["end"]]
    Generated = EncodePadCapPacket(
        KConfigGen, Initial, Owner, Cap, Footprint.Geometry, Depth, Seat
    )
    SavedPayload, SavedModel = CheckPacket(Saved, Initial, Expected)
    FreshPayload, FreshModel = CheckPacket(Generated, Initial, Expected)
    RequireArch(
        (SavedPayload.schema, FreshPayload.schema),
        ("SCH_3701250_37102_13006", "SCH_1200000_12006"),
        "independently decoded saved and generated Parasolid schemas",
    )
    Attribute = "solidworks.unchanged_id"
    NativeAttribute = SavedModel.faces[0].attributes.get(Attribute)
    RequireArch(
        type(NativeAttribute) is int
        and Attribute not in FreshModel.faces[0].attributes,
        True,
        "saved occurrence carries a separate native face attribute",
    )
    return {
        "archive_sha256": Save["sha256"],
        "saved_packet": [
            Span["size"],
            ShaValue(Saved[9:]).hexdigest(),
            SavedPayload.sha256,
        ],
        "generated_packet": [
            len(Generated) - 9,
            ShaValue(Generated[9:]).hexdigest(),
            FreshPayload.sha256,
        ],
        "allocation": Initial.NextIndex,
        "support_ring_mm": Expected,
        "native_unchanged_id": NativeAttribute,
    }


# fresh profile and filed chooser introduce their own allocations and dimensions
def BuildPacketTrial() -> (
    tuple[PartArchiveState, PadCapBoss, SavedCap, SketchGeometry, int]
):
    Writer = PartArchiveWriter()
    Writer.BeginObject("moPart_c", 1)
    Writer.BeginObject(KExtObjectClass, 1)
    Filed = Writer.next_index - 1
    Writer.BeginObject(KExtObjectClass, 1)
    Foreign = Writer.next_index - 1
    Writer.BeginObject("moProfileFeature_c", 1)
    Profile = Writer.next_index - 1
    Writer.BeginObject(KSketchClass, 1)
    Sketch = Writer.next_index - 1
    Writer.BeginObject("sgLineHandle", 1)
    Sides: list[SketchLine] = [
        {
            "member_index": Index,
            "native_id": 71 + Index,
            "flags": 4,
            "point_indices": [Index, (Index + 1) % 4],
        }
        for Index in range(4)
    ]
    Geometry: SketchGeometry = {
        "object_index": Sketch,
        "body_start": 0,
        "geometry_end": 0,
        "next_map_index": Writer.next_index,
        "points_metres": [
            (0.002, 0.006),
            (0.002, 0.035),
            (0.057, 0.035),
            (0.057, 0.006),
        ],
        "point_relation_tallies": [],
        "external_point_references": [],
        "lines": Sides,
        "length_dimensions": [],
        "member_relations": [],
    }
    Writer.BeginObject(KBossClass, 1)
    Owner: PadCapBoss = {
        "object_index": Writer.next_index - 1,
        "file_ref_object": Filed,
        "native_feature_id": 83,
        "profile_object": Profile,
    }
    Writer.BeginObject(KReferenceClass, 1)
    Prefix = Writer.Snapshot()
    Source = PartArchiveWriter(Prefix)
    WriteChoiceCap(Source, KConfigGen, Owner, 0x13572468, 1, (32, 9, 18, 26))
    Chosen = Source.Build()
    Cursor = Prefix.Cursor(Chosen, 0)
    Cap = ReadCap(Cursor, KDefinitionKind, 1, Owner)
    Initial = Source.Snapshot()
    RequireArch(Cursor.Offset, len(Chosen), "fresh chooser boundary")
    RequireArch(TakeCapState(Cursor), Initial, "fresh owned chooser allocation")
    return Initial, Owner, Cap, Geometry, Foreign


# both mismatched archive owners and malformed complete packets must be refused
def CheckPacketTrial() -> dict[str, object]:
    Initial, Owner, Cap, Footprint, Foreign = BuildPacketTrial()
    Seat = PadCapSeat(
        SurfaceKey(Cap["primary"]),
        tuple(SurfaceKey(Edge) for Edge in Cap["edges"]),
        {
            "root_metres": (0, 0, 0.014),
            "normal_world": (0, 0, 1),
            "transform": {"basis": None, "translation_scale": (0, 0, -0.014, 1)},
            "border_metres": (0, 0, 0, 0),
        },
    )
    Expected = (
        (2.0, 6.0, 14.0),
        (2.0, 35.0, 14.0),
        (57.0, 35.0, 14.0),
        (57.0, 6.0, 14.0),
    )
    Fresh = EncodePadCapPacket(KConfigGen, Initial, Owner, Cap, Footprint, 0.014, Seat)
    Payload, _ = CheckPacket(Fresh, Initial, Expected)
    Negative = 0
    BadPlane = Seat.Frame.copy()
    BadPlane["root_metres"] = (0, 0, 0.015)
    ForeignOwner = Owner.copy()
    ForeignOwner["file_ref_object"] = Foreign
    BadSketch = Footprint.copy()
    BadSketch["lines"] = [
        *Footprint["lines"][:3],
        {**Footprint["lines"][3], "point_indices": [0, 2]},
    ]
    for Operation, Geometry, Binding in (
        (ForeignOwner, Footprint, Seat),
        (Owner, Footprint, Replace(Seat, OrderedSides=Seat.OrderedSides[::-1])),
        (Owner, Footprint, Replace(Seat, Frame=BadPlane)),
        (Owner, BadSketch, Seat),
    ):
        try:
            EncodePadCapPacket(
                KConfigGen, Initial, Operation, Cap, Geometry, 0.014, Binding
            )
        except ArchiveError:
            Negative += 1
        else:
            raise ValueError("accepted contradictory cap provenance or footprint")
    WrongRing = bytes(1) + EncodePartition(
        EncodeBrep(MakeCapSheet(Expected[::-1]), partition=False)
    )
    for Altered in (
        PackFields("<iBi", 3, 0, len(WrongRing)) + WrongRing,
        Fresh[:-1],
        Fresh[:-1] + bytes([1]),
        Fresh + bytes(1),
    ):
        try:
            CheckPacket(Altered, Initial, Expected)
        except ArchiveError:
            Negative += 1
        else:
            raise ValueError("accepted contradictory cap packet")
    return {
        "packet_bytes": len(Fresh) - 9,
        "packet_sha256": ShaValue(Fresh[9:]).hexdigest(),
        "schema": Payload.schema,
        "vertices_mm": Expected,
        "allocation": Initial.NextIndex,
        "negative_controls": Negative,
    }


# the report binds exact private custody and public generated geometry facts
def ReportCapPacket(Directory: FilePath) -> dict[str, object]:
    Directory = Directory.resolve(strict=True)
    Native = AuditDiscovery(Directory, KRepository, *KCapturePins, True)
    Evidence = ReadJsonPin(Directory / "report.json", KCapturePins[1])
    return {
        "application_build": Native["application_build"],
        "native_report_sha256": KCapturePins[1],
        "healthy_stock_controls": Native["stock_controls"],
        "native_observations": Native["verified_native_observations"],
        "licensed_archives": {
            Case["variant"]: ReplayPadCapPacket(Directory, Case["save"])
            for Case in Evidence["observations"]["cases"]
        },
        "fresh_control": CheckPacketTrial(),
    }


# the explicit replay command exposes only digests and typed geometry
def RunCapPacket() -> None:
    Parser = ArgumentParser(description=__doc__)
    Parser.add_argument("--run-directory", required=True, type=FilePath)
    print(DumpJson(ReportCapPacket(Parser.parse_args().run_directory), sort_keys=True))


if __name__ == "__main__":
    RunCapPacket()
