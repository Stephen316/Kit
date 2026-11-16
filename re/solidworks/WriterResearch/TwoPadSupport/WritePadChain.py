# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Construct the inherited projected chain at the upper-pad profile boundary."""

from dataclasses import dataclass as Dataclass
from struct import pack as PackFields

from OriginSketch import KObjectList, KSketchClass
from PartArchive import PartArchiveState, PartArchiveWriter
from RectangleCorners import KLineHandle
from RectangleRegion import KRegionClass
from RectangleSupport import KChainClass, KChainFields
from TwoPadRelations.WritePadEqual import ReadPadSides
from WritePadComp import CheckCompOwner
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import EncodeNull, KBigObjectTag
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Resolved.BossChooser import ChooserOwner, SavedCap
from convert.adapters.solidworks.Resolved.ContourSurf import ProfileOwner
from convert.adapters.solidworks.Resolved.FaceIdentity import SurfaceKey
from convert.adapters.solidworks.Sketch.GeometryTypes import SketchGeometry


# a projected member keeps the native id and the earlier filed cap boundary
@Dataclass(frozen=True, slots=True)
class PadChainEdge:
    NativeId: int
    CapSide: tuple[int, int, int, int]


# the active profile resumes after its own complete inline region and earlier chain
def CheckChainMap(
    StateValue: PartArchiveState,
    Profile: ProfileOwner,
    Geometry: SketchGeometry,
    BossOwner: ChooserOwner,
    CapValue: SavedCap,
) -> None:
    Objects = dict(StateValue.Objects)
    ProfileIndex = Profile["profile_object"]
    SketchIndex = Geometry["object_index"]
    NextIndex = StateValue.NextIndex
    PriorChains = tuple(
        Index for Index, Name in StateValue.Objects if Name == KChainClass
    )
    RequireArch(
        type(ProfileIndex) is int
        and type(SketchIndex) is int
        and type(Profile["native_feature_id"]) is int
        and 0 < Profile["native_feature_id"] <= 0x7FFFFFFF
        and Profile["native_feature_id"] != BossOwner["native_feature_id"]
        and 0
        < CapValue["object_index"]
        < ProfileIndex
        < SketchIndex
        < NextIndex
        < KBigObjectTag
        and ProfileIndex
        == max(
            (
                Index
                for Index, Name in StateValue.Objects
                if Name == "moProfileFeature_c"
            ),
            default=-1,
        )
        and SketchIndex
        == max(
            (Index for Index, Name in StateValue.Objects if Name == KSketchClass),
            default=-1,
        )
        and len(PriorChains) == 1
        and PriorChains[0] < BossOwner["object_index"]
        and any(
            Name == KChainClass and Index < PriorChains[0]
            for Index, Name in StateValue.Classes
        ),
        True,
        "active upper profile and inherited earlier chain",
    )
    RegionStart = NextIndex - 7
    RequireArch(
        SketchIndex < Geometry["next_map_index"] <= RegionStart
        and tuple(Objects.get(Index) for Index in range(RegionStart, NextIndex))
        == (KObjectList, KRegionClass, KObjectList, *((KLineHandle,) * 4)),
        True,
        "same closed active upper sketch region before the projected chain",
    )


# the projected ids must be disjoint from local members and follow the proved cap
def BindPadChain(
    Geometry: SketchGeometry,
    CapValue: SavedCap,
    Projected: tuple[PadChainEdge, ...],
) -> tuple[int, ...]:
    Local = ReadPadSides(Geometry)
    RequireArch(
        type(Projected) is tuple
        and len(Projected) == 4
        and all(isinstance(Edge, PadChainEdge) for Edge in Projected),
        True,
        "four typed projected cap boundary bindings",
    )
    Identities = tuple(Edge.NativeId for Edge in Projected)
    RequireArch(
        all(
            type(Identity) is int and 0 < Identity <= 0x7FFFFFFF
            for Identity in Identities
        )
        and len(set(Identities)) == 4
        and set(Identities).isdisjoint(Local),
        True,
        "distinct projected ids outside the local sketch namespace",
    )
    RequireArch(
        all(
            type(Edge.CapSide) is tuple
            and len(Edge.CapSide) == 4
            and all(type(Field) is int for Field in Edge.CapSide)
            for Edge in Projected
        )
        and tuple(Edge.CapSide for Edge in Projected)
        == tuple(SurfaceKey(EdgeValue) for EdgeValue in CapValue["edges"]),
        True,
        "exact earlier cap side identities in contour order",
    )
    return Identities


# the compact chain stops before any embedded geometry is allocated or stored
def EncodePadChain(
    Generation: int,
    StateValue: PartArchiveState,
    Profile: ProfileOwner,
    Geometry: SketchGeometry,
    BossOwner: ChooserOwner,
    CapValue: SavedCap,
    Projected: tuple[PadChainEdge, ...],
) -> tuple[bytes, PartArchiveState]:
    RequireArch(Generation, KConfigGen, "upper-pad projected chain generation")
    CheckCompOwner(StateValue, BossOwner, CapValue)
    CheckChainMap(StateValue, Profile, Geometry, BossOwner, CapValue)
    Edges = BindPadChain(Geometry, CapValue, Projected)
    Writer = PartArchiveWriter(StateValue)
    Writer.raw(PackFields("<Ii", 1, 1))
    Writer.BeginObject(KChainClass, 1)
    Writer.raw(PackFields("<H4IHI6i", 4, *Edges, 1, 0, *KChainFields))
    Writer.string("")
    Writer.raw(PackFields("<H2I", 0, 0xFFFFFFFF, 0))
    Writer.raw(EncodeNull() * 2)
    Writer.raw(PackFields("<3i", 0, 0, 0))
    return Writer.Build(), Writer.Snapshot()
