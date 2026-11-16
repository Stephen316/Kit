# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Generate an offline two-pad support sheet from its own cap and rectangle."""

from dataclasses import dataclass as Dataclass
from math import hypot as Hypot, isfinite as IsFinite
from struct import pack as PackFields
from typing import TypeAlias

from OriginSketch import KSketchClass
from PartArchive import PartArchiveState
from TwoPadRelations.WritePadEqual import ReadPadSides
from WritePadComp import CheckCompOwner
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Parasolid import EncodeBrep, EncodePartition
from convert.adapters.solidworks.Resolved.BossChooser import ChooserOwner, SavedCap
from convert.adapters.solidworks.Resolved.FaceIdentity import SurfaceKey
from convert.adapters.solidworks.Resolved.Support.FaceFrame import FaceFrame
from convert.adapters.solidworks.Sketch.GeometryTypes import SketchGeometry
from interchange.brep.Curves.BrepCurves import LineCurve
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.brep.Topology.BrepTopology import (
    BrepBody,
    BrepCoedge,
    BrepEdge,
    BrepFace,
    BrepFaceUse,
    BrepLoop,
    BrepRegion,
    BrepShell,
    BrepShellUse,
    BrepVertex,
)
from interchange.geometry.Models.VectorSpace import SpaceVector

# spatial positions use the millimetre contract of the neutral brep model
CapPoint: TypeAlias = tuple[float, float, float]

# archived cap references carry an independent tuple of filed ownership words
CapIdentity: TypeAlias = tuple[int, int, int, int]


# the lower operation must retain its original rectangle profile allocation
class PadCapBoss(ChooserOwner):
    profile_object: int


# the later support independently identifies the earlier cap and its world pose
@Dataclass(frozen=True, slots=True)
class PadCapSeat:
    Primary: CapIdentity
    OrderedSides: tuple[CapIdentity, ...]
    Frame: FaceFrame


# lower sketch and support identities must agree before constructing any topology
def BindPadSeat(
    StateValue: PartArchiveState,
    Owner: PadCapBoss,
    CapValue: SavedCap,
    Geometry: SketchGeometry,
    Depth: float,
    Seat: PadCapSeat,
) -> None:
    CheckCompOwner(StateValue, Owner, CapValue)
    Objects = dict(StateValue.Objects)
    ProfileIndex = Owner["profile_object"]
    SketchIndex = Geometry["object_index"]
    RequireArch(
        type(SketchIndex) is int
        and type(ProfileIndex) is int
        and 0 < ProfileIndex < SketchIndex < Owner["object_index"]
        and tuple(
            Index
            for Index in range(ProfileIndex, Owner["object_index"])
            if Objects.get(Index) in ("moProfileFeature_c", KSketchClass)
        )
        == (ProfileIndex, SketchIndex)
        and Objects.get(ProfileIndex) == "moProfileFeature_c"
        and Objects.get(SketchIndex) == KSketchClass
        and SketchIndex < Geometry["next_map_index"] <= Owner["object_index"],
        True,
        "earlier boss owns the reached lower rectangle sketch",
    )
    RequireArch(
        (Seat.Primary, Seat.OrderedSides),
        (
            SurfaceKey(CapValue["primary"]),
            tuple(SurfaceKey(Side) for Side in CapValue["edges"]),
        ),
        "support is the same filed top cap and ordered perimeter",
    )
    RequireArch(
        type(Depth) is float and IsFinite(Depth * 1000) and Depth > 0,
        True,
        "positive finite lower-pad depth",
    )
    Frame = Seat.Frame
    RequireArch(
        (
            Frame["root_metres"],
            Frame["normal_world"],
            Frame["transform"]["basis"],
            Frame["transform"]["translation_scale"],
        ),
        ((0, 0, Depth), (0, 0, 1), None, (0, 0, -Depth, 1)),
        "selected support plane matches the positive XY cap",
    )


# the lower directed ring follows its owned four sides at the support depth
def MakeCapRing(Geometry: SketchGeometry, Depth: float) -> tuple[CapPoint, ...]:
    Points = {Point for Side in ReadPadSides(Geometry).values() for Point in Side}
    Left, Right = sorted({X for X, _ in Points})
    Bottom, Top = sorted({Y for _, Y in Points})
    Ring = (
        (Left * 1000, Bottom * 1000, Depth * 1000),
        (Left * 1000, Top * 1000, Depth * 1000),
        (Right * 1000, Top * 1000, Depth * 1000),
        (Right * 1000, Bottom * 1000, Depth * 1000),
    )
    RequireArch(
        all(IsFinite(Value) for Point in Ring for Value in Point)
        and IsFinite(Ring[2][0] - Ring[0][0])
        and IsFinite(Ring[2][1] - Ring[0][1])
        and Ring[0][0] < Ring[2][0]
        and Ring[0][1] < Ring[2][1],
        True,
        "four distinct finite support corners",
    )
    return Ring


# the linear carrier and coedge retain the neutral direction of one boundary
def MakeCapSide(
    Index: int,
    Start: BrepVertex,
    End: BrepVertex,
) -> tuple[LineCurve, BrepEdge, BrepCoedge]:
    Rise = (
        End.point.x - Start.point.x,
        End.point.y - Start.point.y,
        End.point.z - Start.point.z,
    )
    Length = Hypot(*Rise)
    Curve = LineCurve(
        f"curve-{Index}",
        Start.point,
        SpaceVector(Rise[0] / Length, Rise[1] / Length, Rise[2] / Length),
    )
    Edge = BrepEdge(f"edge-{Index}", Start.id, End.id, Curve.id, 0.0, Length)
    return Curve, Edge, BrepCoedge(f"coedge-{Index}", Edge.id)


# a single open shell has one reversed planar face and no enclosed material
def MakeCapSheet(Ring: tuple[CapPoint, ...]) -> BrepModel:
    Vertices = tuple(
        BrepVertex(f"point-{Index}", SpaceVector(*Point))
        for Index, Point in enumerate(reversed(Ring))
    )
    Sides = tuple(
        MakeCapSide(Index, Start, End)
        for Index, (Start, End) in enumerate(
            zip(Vertices, Vertices[1:] + Vertices[:1], strict=True)
        )
    )
    Surface = PlaneSurface(
        "surface",
        SpaceVector(0, 0, Ring[0][2]),
        SpaceVector(0, 0, -1),
        SpaceVector(-1, 0, 0),
    )
    return BrepModel(
        curves=tuple(Curve for Curve, _, _ in Sides),
        surfaces=(Surface,),
        vertices=Vertices,
        edges=tuple(Edge for _, Edge, _ in Sides),
        coedges=tuple(Coedge for _, _, Coedge in Sides),
        loops=(BrepLoop("ring", tuple(Row[2].id for Row in Sides), True),),
        faces=(BrepFace("face", Surface.id, ("ring",), False),),
        face_uses=(BrepFaceUse("face-use", "face"),),
        shells=(BrepShell("shell", ("face-use",), False),),
        shell_uses=(BrepShellUse("shell-use", "shell"),),
        regions=(BrepRegion("region", ("shell-use",), False),),
        bodies=(BrepBody("sheet", ("region",)),),
    )


# the packet is an inline compressed transmit and leaves the archive map intact
def EncodePadCapPacket(
    Generation: int,
    StateValue: PartArchiveState,
    Owner: PadCapBoss,
    CapValue: SavedCap,
    Geometry: SketchGeometry,
    Depth: float,
    Seat: PadCapSeat,
) -> bytes:
    RequireArch(Generation, KConfigGen, "upper-pad support packet generation")
    BindPadSeat(StateValue, Owner, CapValue, Geometry, Depth, Seat)
    Sheet = MakeCapSheet(MakeCapRing(Geometry, Depth))
    Packet = bytes(1) + EncodePartition(EncodeBrep(Sheet, partition=False))
    return PackFields("<iBi", 3, 0, len(Packet)) + Packet
