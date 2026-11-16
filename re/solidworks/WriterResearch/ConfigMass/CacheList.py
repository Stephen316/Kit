# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as Dataclass

from CmgrBossMass import EncodeBossMass, Point
from ConfigAtomManager import ConfigAtomBinding, KAtomClass, RequireBossBody
from PartArchive import PartArchiveWriter
from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch


# The live cache shares the generated atom and body-update stamp with its owning part.
@Dataclass(frozen=True, slots=True)
class RectMassCache:
    Binding: ConfigAtomBinding
    BodyStamp: int
    MinimumM: Point
    MaximumM: Point
    DensityKgM3: float


# The model stores occupied cache slots in order, including one invalidated first slot.
def WriteMassList(
    Writer: PartArchiveWriter,
    Generation: int,
    CacheValue: RectMassCache | None,
    HasStaleSlot: bool = False,
) -> None:
    RequireArch(
        type(Generation) is int
        and Generation == KConfigGen
        and type(HasStaleSlot) is bool,
        True,
        "ordinary generation-19000 mass cache list",
    )
    AtomSlots = tuple(
        Slot for Slot, Name in Writer.objects.items() if Name == KAtomClass
    )
    if CacheValue is None:
        RequireArch(
            not HasStaleSlot and not AtomSlots,
            True,
            "standalone sketch without cache slots",
        )
        Writer.i32(0)
        return

    Binding = CacheValue.Binding
    RequireBossBody(Binding.Body)
    RequireArch(
        all(
            type(Value) is int and 0 < Value <= 0x7FFFFFFF
            for Value in (Binding.AtomId, Binding.ObjectIndex, CacheValue.BodyStamp)
        )
        and AtomSlots == (Binding.ObjectIndex,),
        True,
        "allocated model atom and positive body stamp",
    )
    MassRecord = EncodeBossMass(
        Generation, 1, CacheValue.MinimumM, CacheValue.MaximumM, CacheValue.DensityKgM3
    )
    SlotCount = 1 + int(HasStaleSlot)
    Writer.i32(SlotCount)
    if HasStaleSlot:
        Writer.i32(0)
    Writer.i32(1)
    Writer.i32(Binding.AtomId)
    Writer.i32(CacheValue.BodyStamp)
    Writer.f64(CacheValue.DensityKgM3)
    Writer.raw(MassRecord)
    if HasStaleSlot:
        Writer.i32(SlotCount % 2)
