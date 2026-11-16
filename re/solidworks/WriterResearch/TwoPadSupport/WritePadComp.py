# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Construct the matched-owner component prefix of a two-pad face reference."""

from dataclasses import dataclass as Dataclass
from struct import pack as PackFields

from BossChoice import KFaceClass
from BossOpen import KBossClass
from ConfigAtomManager import ConfigAtomBinding, KAtomClass, RequireBossBody
from LocalComponent import (
    CheckLocalComponent,
    KComponentTail,
    KPartClass,
    KUnitComponent,
)
from PartArchive import PartArchiveState, PartArchiveWriter
from WritePadCap import CheckCapIds
from convert.adapters.solidworks.Container.Archive import ArchiveError, KBigObjectTag
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Cmgr import KExtObjectClass
from convert.adapters.solidworks.Resolved.BossChooser import ChooserOwner, SavedCap

# the prefix materializes the first local component face before its face header
KCompFaceClass = "moCompFace_c"

# the selected face resolver sets this flag after confirming its owner atom
KMatchedAtomFlag = 0x4000


# the supplied branch evidence must identify the same local selection and owner
@Dataclass(frozen=True, slots=True)
class PadCompMatch:
    PartObject: int
    CapObject: int
    TransferObject: int
    AtomId: int


# the previous chooser must still refer to the exact authored lower extrusion
def CheckCompOwner(
    StateValue: PartArchiveState, Owner: ChooserOwner, CapValue: SavedCap
) -> None:
    Objects = dict(StateValue.Objects)
    CapIndex = CapValue["object_index"]
    EarlierBoss = max(
        (
            Index
            for Index, Name in StateValue.Objects
            if Index < CapIndex and Name == KBossClass
        ),
        default=-1,
    )
    FileIndex = Owner["file_ref_object"]
    RequireArch(
        EarlierBoss == Owner["object_index"]
        and type(FileIndex) is int
        and 0 < FileIndex < EarlierBoss
        and type(Owner["native_feature_id"]) is int
        and Objects.get(FileIndex) == KExtObjectClass
        and Objects.get(CapIndex) == KFaceClass
        and CapValue["classifier"] == 0,
        True,
        "reached earlier boss chooser",
    )
    CheckCapIds(StateValue, Owner, CapValue)


# a distinct transfer and local part witness the selected body before allocation
def CheckCompMatch(
    StateValue: PartArchiveState,
    PartObject: int,
    Owner: ChooserOwner,
    CapValue: SavedCap,
    SourceAtom: ConfigAtomBinding,
    MatchValue: PadCompMatch | None,
) -> None:
    if not isinstance(MatchValue, PadCompMatch):
        raise ArchiveError("missing matched cap owner evidence")
    RequireBossBody(SourceAtom.Body)
    RequireArch(
        all(
            type(Value) is int and Value > 0
            for Value in (
                MatchValue.PartObject,
                MatchValue.CapObject,
                MatchValue.TransferObject,
                MatchValue.AtomId,
            )
        ),
        True,
        "typed matched cap owner evidence",
    )
    Objects = dict(StateValue.Objects)
    RequireArch(
        type(SourceAtom.AtomId) is int
        and 0 < SourceAtom.AtomId <= 0x7FFFFFFF
        and type(SourceAtom.ObjectIndex) is int
        and PartObject < SourceAtom.ObjectIndex < Owner["object_index"]
        and Objects.get(SourceAtom.ObjectIndex) == KAtomClass
        and SourceAtom.Body.FeatureId == Owner["native_feature_id"],
        True,
        "the selected earlier configuration atom owns the cap",
    )
    RequireArch(
        MatchValue,
        PadCompMatch(
            PartObject,
            CapValue["object_index"],
            SourceAtom.ObjectIndex,
            SourceAtom.AtomId,
        ),
        "same matched part cap and transfer identity",
    )


# emitting the matched branch stops before the separately owned face header
def EncodePadComp(
    Generation: int,
    StateValue: PartArchiveState,
    PartObject: int,
    Owner: ChooserOwner,
    CapValue: SavedCap,
    SourceAtom: ConfigAtomBinding,
    MatchValue: PadCompMatch | None,
) -> tuple[bytes, PartArchiveState]:
    Writer = PartArchiveWriter(StateValue)
    CheckLocalComponent(Writer, Generation, PartObject)
    CheckCompOwner(StateValue, Owner, CapValue)
    CheckCompMatch(StateValue, PartObject, Owner, CapValue, SourceAtom, MatchValue)
    RequireArch(
        KCompFaceClass not in Writer.classes
        and StateValue.NextIndex + 2 < KBigObjectTag,
        True,
        "first compact face component allocation",
    )
    Writer.BeginObject(KCompFaceClass, 1)
    Writer.BeginObject(KUnitComponent, 1)
    Writer.ReferenceObject(PartObject, KPartClass)
    AtomId = SourceAtom.AtomId
    Writer.raw(
        PackFields(
            "<B20iB",
            0,
            KMatchedAtomFlag,
            AtomId,
            AtomId,
            0,
            *KComponentTail,
            Generation,
            0,
        )
    )
    return Writer.Build(), Writer.Snapshot()
