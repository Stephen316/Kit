# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as Dataclass

from ConfigAtomManager import (
    KAtomClass,
    BossAtomBody,
    ConfigAtomBinding,
    ReadBossAtom,
    RequireBossBody,
    WriteBossAtom,
)
from ConfigMaterial import KModelDataClass
from ConfigSplitEdges import KInitialAtomCounter, RequireGeneration
from PartArchive import PartArchiveWriter
from convert.adapters.solidworks.Container.Archive import KBigObjectTag
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import ArchiveCursor


# the two feature owners each refer to the same joined kernel solid
@Dataclass(frozen=True, slots=True)
class PadAtomOwners:
    BaseFeature: int
    UpperFeature: int
    MergedSolidTag: int


# feature order differs from the configured archive occurrence order
@Dataclass(frozen=True, slots=True)
class PadAtomBindings:
    Base: ConfigAtomBinding
    Upper: ConfigAtomBinding


# identities allocate in feature order even though the upper record files first
KBaseAtom = KInitialAtomCounter + 1

# the latest allocated identity is also the filed counter
KUpperAtom = KBaseAtom + 1


# preflight requires a clean compact map with room for the class and two objects
def RequirePadMap(Classes: set[str], NextIndex: int, Generation: int) -> None:
    RequireGeneration(Generation)
    RequireArch(
        KModelDataClass in Classes and KAtomClass not in Classes,
        True,
        "merged-pad manager begins on the filed model map",
    )
    RequireArch(NextIndex + 2 < KBigObjectTag, True, "compact merged-pad slots")


# validate both owners before filing the manager or allocating either object
def WritePadAtoms(
    Writer: PartArchiveWriter, Generation: int, Owners: PadAtomOwners
) -> PadAtomBindings:
    RequirePadMap(set(Writer.classes), Writer.next_index, Generation)
    BaseBody = BossAtomBody(Owners.BaseFeature, Owners.MergedSolidTag)
    UpperBody = BossAtomBody(Owners.UpperFeature, Owners.MergedSolidTag)
    RequireBossBody(BaseBody)
    RequireBossBody(UpperBody)
    RequireArch(BaseBody.FeatureId != UpperBody.FeatureId, True, "distinct pad owners")

    Writer.u16(0)  # the root feature list files in the resolved stream
    Writer.i32(0)  # enclosing node list return
    Writer.i32(KUpperAtom)
    Writer.i32(2)
    Upper = WriteBossAtom(Writer, KUpperAtom, UpperBody)
    Base = WriteBossAtom(Writer, KBaseAtom, BaseBody, Flags=1)
    Writer.u32(Generation)
    return PadAtomBindings(Base, Upper)


# readback binds the older atom to its class reference and the same joined solid
def ReadPadAtoms(Cursor: ArchiveCursor, Generation: int) -> PadAtomBindings:
    RequirePadMap(set(Cursor.Classes.values()), Cursor.NextIndex, Generation)
    RequireArch(
        Cursor.ReadInts("<Hiii"), (0, 0, KUpperAtom, 2), "merged-pad list opening"
    )
    Upper = ReadBossAtom(Cursor, KUpperAtom)
    Base = ReadBossAtom(Cursor, KBaseAtom, Flags=1)
    RequireArch(
        Base.Body.FeatureId != Upper.Body.FeatureId, True, "distinct pad owners"
    )
    RequireArch(
        Base.Body.SolidBodyTag, Upper.Body.SolidBodyTag, "one joined kernel solid"
    )
    RequireArch(Cursor.ReadInts("<I"), (Generation,), "merged-pad generation return")
    return PadAtomBindings(Base, Upper)
