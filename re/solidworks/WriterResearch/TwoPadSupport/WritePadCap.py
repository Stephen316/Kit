# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Write the persistent occurrence of a reached upper-pad support cap."""

from BossChoice import EndChoiceFace, KFaceClass, WriteChoiceId
from BossOpen import KBossClass
from PartArchive import PartArchiveState, PartArchiveWriter
from RectangleTrim import KReferenceClass
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Archive import KBigObjectTag
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Cmgr import KExtObjectClass
from convert.adapters.solidworks.Resolved.BossChooser import ChooserOwner, SavedCap
from convert.adapters.solidworks.Resolved.FaceIdentity import (
    KCapClass,
    KEdgeClass,
    KSurfaceId,
    SurfaceKey,
)


# the source face must belong to the preceding extrusion and its original filed part
def CheckCapOwner(
    StateValue: PartArchiveState, Owner: ChooserOwner, CapValue: SavedCap
) -> None:
    Objects = dict(StateValue.Objects)
    FaceIndex = CapValue["object_index"]
    PreviousBoss = max(
        (
            Index
            for Index, Name in StateValue.Objects
            if Index < FaceIndex and Name == KBossClass
        ),
        default=-1,
    )
    NativeId = Owner["native_feature_id"]
    FileIndex = Owner["file_ref_object"]
    RequireArch(
        PreviousBoss == Owner["object_index"]
        and 0 < FileIndex < PreviousBoss
        and Objects.get(FileIndex) == KExtObjectClass
        and Objects.get(FaceIndex) == KFaceClass
        and CapValue["classifier"] == 0
        and type(NativeId) is int
        and 0 < NativeId <= 0x7FFFFFFF,
        True,
        "earlier boss chooser and filed owner",
    )
    RequireArch(
        {KCapClass, KEdgeClass, KReferenceClass}
        <= {Name for _, Name in StateValue.Classes}
        and StateValue.NextIndex + 9 < KBigObjectTag,
        True,
        "ten later compact occurrence slots",
    )


# distinct ordered allocations bind all five identities to the selected top cap
def CheckCapIds(
    StateValue: PartArchiveState, Owner: ChooserOwner, CapValue: SavedCap
) -> tuple[KSurfaceId, ...]:
    Objects = dict(StateValue.Objects)
    Primary = CapValue["primary"]
    Edges = CapValue["edges"]
    EdgeIds = tuple(Edge["occurrence"] for Edge in Edges)
    TimeWord = Primary["time_word"]
    RequireArch(
        Primary["occurrence"] == 1
        and type(TimeWord) is int
        and 0 <= TimeWord < 0xFFFFFFFF
        and len(EdgeIds) == len(set(EdgeIds)) == 4
        and all(type(EdgeId) is int and 0 < EdgeId <= 0x7FFFFFFF for EdgeId in EdgeIds),
        True,
        "top-cap selector and four different boundary occurrences",
    )
    Identities = (Primary, *Edges)
    Previous = CapValue["object_index"]
    for Surface, ClassName in zip(
        Identities, (KCapClass,) + (KEdgeClass,) * len(Edges), strict=True
    ):
        SlotIndex = Surface["object_index"]
        Reference = Surface["feature_ref_object"]
        RequireArch(
            Previous < SlotIndex < Reference < StateValue.NextIndex
            and Reference == SlotIndex + 1
            and Surface["class"] == Objects.get(SlotIndex) == ClassName
            and Objects.get(Reference) == KReferenceClass
            and SurfaceKey(Surface)[:3]
            == (Owner["file_ref_object"], Owner["native_feature_id"], TimeWord),
            True,
            "ordered typed chooser occurrence belongs to the earlier boss",
        )
        Previous = Reference
    return Identities


# generate the identities after a caller supplies the containing face header
def EncodePadCap(
    Generation: int,
    StateValue: PartArchiveState,
    Owner: ChooserOwner,
    CapValue: SavedCap,
) -> tuple[bytes, PartArchiveState]:
    RequireArch(Generation, KConfigGen, "upper-pad cap occurrence generation")
    CheckCapOwner(StateValue, Owner, CapValue)
    Identities = CheckCapIds(StateValue, Owner, CapValue)
    Writer = PartArchiveWriter(StateValue)
    for Surface in Identities:
        WriteChoiceId(
            Writer, Owner, Surface["time_word"], Surface["class"], Surface["occurrence"]
        )
    EndChoiceFace(Writer, Generation)
    return Writer.Build(), Writer.Snapshot()
