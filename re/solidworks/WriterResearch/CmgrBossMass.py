# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as Dataclass
from math import isfinite as IsFinite

from CmgrMass import EncodeMassRecord, ReadMassOptions
from convert.adapters.solidworks.Container.Archive import ArchiveError
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor

Point = tuple[float, float, float]
KDefaultAccuracy = 0.995


@Dataclass(frozen=True, slots=True)
class BossMass:
    CentroidM: Point
    VolumeM3: float
    AreaM2: float
    MassKg: float
    MomentXyzKgM2: Point
    ProductMoments: Point


# The caller supplies the world bounds of a proven aligned cuboid.
def CalcBossMass(MinimumM: Point, MaximumM: Point, DensityKgM3: float) -> BossMass:
    if (
        isinstance(DensityKgM3, bool)
        or not IsFinite(DensityKgM3)
        or DensityKgM3 <= 0.0
    ):
        raise ArchiveError("rectangular boss density must be positive and finite")
    LoX, LoY, LoZ = MinimumM
    HiX, HiY, HiZ = MaximumM
    Dx, Dy, Dz = HiX - LoX, HiY - LoY, HiZ - LoZ
    if not all(IsFinite(Span) and Span > 0.0 for Span in (Dx, Dy, Dz)):
        raise ArchiveError("rectangular boss spans must be positive and finite")

    Center = (LoX + Dx / 2, LoY + Dy / 2, LoZ + Dz / 2)
    Volume = Dx * Dy * Dz
    Area = 2 * (Dx * Dy + Dy * Dz + Dz * Dx)
    Mass = DensityKgM3 * Volume
    Moments = (
        Mass * (Dy * Dy + Dz * Dz) / 12,
        Mass * (Dx * Dx + Dz * Dz) / 12,
        Mass * (Dx * Dx + Dy * Dy) / 12,
    )
    if not all(IsFinite(Value) and Value > 0.0 for Value in (Volume, Area, Mass, *Moments)):
        raise ArchiveError("rectangular boss properties exceed finite positive range")
    return BossMass(Center, Volume, Area, Mass, Moments, (0.0, 0.0, 0.0))


# The shared archive order differs from the native member order for two products.
def BossMassFields(Value: BossMass) -> tuple[float, ...]:
    return (
        *Value.CentroidM,
        Value.VolumeM3,
        Value.AreaM2,
        Value.MassKg,
        *Value.MomentXyzKgM2,
        *Value.ProductMoments,
    )


# A single uniform solid needs no merged body or coordinate override state.
def RequireBossMassScope(Generation: int, BodyCount: int) -> None:
    RequireArch(
        (type(Generation), Generation, type(BodyCount), BodyCount),
        (int, 19000, int, 1),
        "ordinary single solid mass scope",
    )


# The caller has already proved the bounds belong to one aligned rectangular boss.
def EncodeBossMass(
    Generation: int,
    BodyCount: int,
    MinimumM: Point,
    MaximumM: Point,
    DensityKgM3: float,
) -> bytes:
    RequireBossMassScope(Generation, BodyCount)
    Value = CalcBossMass(MinimumM, MaximumM, DensityKgM3)
    return EncodeMassRecord(BossMassFields(Value), KDefaultAccuracy)


# The captured cache keeps the kernel residuals for comparison with generated values.
def ReadBossMass(
    Cursor: FieldCursor, Generation: int, BodyCount: int
) -> BossMass:
    RequireBossMassScope(Generation, BodyCount)
    X, Y, Z, Volume, Area, Mass, XX, YY, ZZ, XY, XZ, YZ = Cursor.ReadPoint(12)
    RequireArch(
        all(Value > 0.0 for Value in (Volume, Area, Mass, XX, YY, ZZ)),
        True,
        "positive solid mass fields",
    )
    ReadMassOptions(Cursor, KDefaultAccuracy)
    return BossMass((X, Y, Z), Volume, Area, Mass, (XX, YY, ZZ), (XY, XZ, YZ))
