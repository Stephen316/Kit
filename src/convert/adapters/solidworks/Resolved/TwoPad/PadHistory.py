# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Config.OrdinaryMap import ReadEmptyMap
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.Resolved.BossEnd import BossClose, ReadBossClose
from convert.adapters.solidworks.Resolved.BossEntry import (
    BossHead,
    ReadBossHead,
    ReadOpNode,
)
from convert.adapters.solidworks.Resolved.ContourChain import ReadChainState
from convert.adapters.solidworks.Resolved.ContourSurf import ProfileOwner
from convert.adapters.solidworks.Resolved.ContourTrim import ReadRectEnd, ReadRectTrim
from convert.adapters.solidworks.Resolved.Cut.CutEdgeRef import CheckCutEdges
from convert.adapters.solidworks.Resolved.Cut.CutOpRead import CutOperation, ReadCutOp
from convert.adapters.solidworks.Resolved.Cut.CutProfileBody import ReadCutBody
from convert.adapters.solidworks.Resolved.Cut.CutProfileSeal import ReadCutSeal
from convert.adapters.solidworks.Resolved.OriginProfile import ReadOrigin
from convert.adapters.solidworks.Resolved.ProfilePlane import ReadProfileRef
from convert.adapters.solidworks.Resolved.ProfileSketch import (
    ProfileSketch,
    ReadProfileBody,
)
from convert.adapters.solidworks.Resolved.RectanglePart import ResolveDatum
from convert.adapters.solidworks.Resolved.ResolvedHead import OpenResolved
from convert.adapters.solidworks.Resolved.Support.SupportPlane import (
    RequireFaceCap,
    ReadFaceSupport,
    SupportPlane,
)
from convert.adapters.solidworks.Resolved.SystemPrefix import ReadSysPrefix
from convert.adapters.solidworks.Resolved.TwoPad.PadProfile import (
    PadLinePair,
    ReadPadProfMut,
)

# the two pad route uses the short resolved list and two configured atoms
KPadListCount = 21


# the attached pad must keep its own profile and the fully proven earlier producer
@Dataclass(frozen=True, slots=True)
class PadHistory:
    BaseValue: BossHead
    BaseEnd: BossClose
    UpperProfile: ProfileSketch
    UpperPair: PadLinePair
    UpperValue: CutOperation
    Support: SupportPlane


# the lower boss must own an inline rectangle on the saved datum and a positive end
def ReadBasePad(Cursor: ArchiveCursor) -> tuple[BossHead, BossClose]:
    System = ReadSysPrefix(Cursor)
    Origin = ReadOrigin(Cursor, KConfigGen)
    RequireArch(
        Origin.Support.FeatureId, System.Planes[0].FeatureId, "resolved front origin"
    )
    Profile = ReadProfileBody(Cursor, KConfigGen)
    LineIds = tuple(
        LineValue["native_id"]
        for LineValue in Profile.Geometry["lines"]
        if LineValue["native_id"] >= 0
    )
    _ = ReadChainState(Cursor, True, LineIds)
    Reference = ReadProfileRef(Cursor, KConfigGen)
    Datum, Directions = ResolveDatum(Reference, System.Planes)
    RequireArch(
        (Datum.Geometry.PointMetres, Directions[2]),
        ((0, 0, 0), (0, 0, 1)),
        "base starts on the saved XY datum",
    )
    Owner: ProfileOwner = {
        "profile_object": Profile.ObjectIndex,
        "native_feature_id": Profile.FeatureId,
    }
    TrimValue = ReadRectTrim(Cursor, Owner, LineIds, 1)
    _ = ReadRectEnd(Cursor, True)
    FileObject = TrimValue["trim_surface"]["file_reference"]["object_index"]
    NodeValue = ReadOpNode(
        Cursor,
        "moExtrusion_c",
        (0x40000140, 0xC0000140),
        Profile.ObjectIndex,
        FileObject,
    )
    BossValue = ReadBossHead(Cursor, NodeValue, (0,))
    EndValue = ReadBossClose(Cursor)
    RequireArch(
        EndValue["depth_display"]["dimension"]["metres"] > 0,
        True,
        "positive base-pad depth",
    )
    return BossValue, EndValue


# the reached upper contour and adjacent local pose both prove the same selected cap
def ReadPadSupport(
    Cursor: ArchiveCursor,
    Profile: ProfileSketch,
    BaseValue: BossHead,
    BaseEnd: BossClose,
) -> SupportPlane:
    CapValue = BaseValue["choosers"]["caps"][1]
    BodyValue = ReadCutBody(Cursor, Profile.SketchIndex)
    CheckCutEdges(BodyValue["edge_references"], CapValue)
    Support = ReadFaceSupport(Cursor, KConfigGen, 0)
    RequireFaceCap(Support, CapValue)
    Frame = Support["face"]["plane"]
    BaseDepth = BaseEnd["depth_display"]["dimension"]["metres"]
    RequireArch(
        (Frame["root_metres"], Frame["normal_world"]),
        ((0, 0, BaseDepth), (0, 0, 1)),
        "upper-pad cap at base end",
    )
    RequireArch(
        Support["reference_point_metres"][2],
        BaseDepth,
        "upper reference atom lies on the reached cap",
    )
    Owner: ProfileOwner = {
        "profile_object": Profile.ObjectIndex,
        "native_feature_id": Profile.FeatureId,
    }
    SealValue = ReadCutSeal(Cursor, Owner, BaseValue["file_ref_object"], MergeMode=True)
    RequireArch(SealValue["state_word"], 103, "witnessed upper-pad trim state")
    RequireArch(
        SealValue["placement"],
        Frame["transform"],
        "upper sketch agrees with saved face transform",
    )
    LineIds = {
        LineValue["native_id"]
        for LineValue in Profile.Geometry["lines"]
        if LineValue["native_id"] >= 0
    }
    TrimIds = {EdgeValue["edge_id"] for EdgeValue in SealValue["trim_edges"]}
    ChainIds = set(BodyValue["chain"]["edge_ids"])
    RequireArch(
        (len(LineIds), LineIds.isdisjoint(ChainIds), TrimIds),
        (4, True, ChainIds | LineIds),
        "upper-pad trim owns the local and projected boundaries",
    )
    return Support


# the face proof is usable only after a terminal merge owns the contour and reached body
def ReadPadHistory(ConfigData: bytes, Resolved: bytes) -> PadHistory:
    MapValue, _ = ReadEmptyMap(ConfigData, (2,))
    Cursor = OpenResolved(Resolved, MapValue, KPadListCount)
    BaseValue, BaseEnd = ReadBasePad(Cursor)
    Profile, PairValue = ReadPadProfMut(Cursor)
    Support = ReadPadSupport(Cursor, Profile, BaseValue, BaseEnd)
    NodeValue = ReadOpNode(
        Cursor,
        "moICE_c",
        (0x40000140, 0xC0000140),
        Profile.ObjectIndex,
        BaseValue["file_ref_object"],
    )
    Transfers = frozenset(
        Index
        for Index, ClassName in MapValue.Objects.items()
        if ClassName == "moAtom_c"
    )
    Upper = ReadCutOp(Cursor, NodeValue, BaseValue, Transfers, MergeMode=True)
    RequireArch(
        BaseValue["native_feature_id"] != NodeValue["native_feature_id"],
        True,
        "distinct pad producers",
    )
    RequireArch(
        Upper["solid_body"]["part_object"],
        Support["part_object"],
        "same upper-pad support and result part",
    )
    return PadHistory(BaseValue, BaseEnd, Profile, PairValue, Upper, Support)
