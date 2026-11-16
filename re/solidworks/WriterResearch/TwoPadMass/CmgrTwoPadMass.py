# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Construct the bounded generation-19000 mass subrecord for two merged pads."""

from dataclasses import dataclass
from math import isfinite, ulp

from CmgrBossMass import (
    KDefaultAccuracy,
    BossMass,
    BossMassFields,
    CalcBossMass,
    Point,
    RequireBossMassScope,
)
from CmgrMass import EncodeMassRecord
from convert.adapters.solidworks.Container.Archive import ArchiveError


# the caller proves each pair of points bounds one world-aligned rectangular pad
@dataclass(frozen=True, slots=True)
class PadBounds:
    Minimum: Point
    Maximum: Point


# the contact face is strictly inside the base top and shares its world center
def CheckPadPlacement(
    Base: PadBounds, Upper: PadBounds, BaseMass: BossMass, UpperMass: BossMass
) -> None:
    if Base.Minimum[2] != 0.0 or Base.Maximum[2] != Upper.Minimum[2]:
        raise ArchiveError(
            "two-pad mass requires an XY base and exact top-face contact"
        )
    if not all(
        Base.Minimum[Axis]
        < Upper.Minimum[Axis]
        < Upper.Maximum[Axis]
        < Base.Maximum[Axis]
        for Axis in (0, 1)
    ):
        raise ArchiveError("two-pad mass requires an upper footprint inside the base")
    if not all(
        abs(Lower - Higher) <= 4 * max(ulp(Lower), ulp(Higher))
        for Lower, Higher in zip(
            BaseMass.CentroidM[:2], UpperMass.CentroidM[:2], strict=True
        )
    ):
        raise ArchiveError("two-pad mass requires coaxial rectangular prisms")


# parallel-axis shifts and the buried contact make the pair one physical body
def CalcTwoPadMass(Base: PadBounds, Upper: PadBounds, DensityKgM3: float) -> BossMass:
    Lower = CalcBossMass(Base.Minimum, Base.Maximum, DensityKgM3)
    Higher = CalcBossMass(Upper.Minimum, Upper.Maximum, DensityKgM3)
    CheckPadPlacement(Base, Upper, Lower, Higher)
    Mass = Lower.MassKg + Higher.MassKg
    if not isfinite(Mass):
        raise ArchiveError("two-pad total mass must be finite")
    CenterZ = (
        Lower.MassKg / Mass * Lower.CentroidM[2]
        + Higher.MassKg / Mass * Higher.CentroidM[2]
    )
    Shift = (
        Lower.MassKg * (Lower.CentroidM[2] - CenterZ) ** 2
        + Higher.MassKg * (Higher.CentroidM[2] - CenterZ) ** 2
    )
    LowerX, LowerY, LowerZ = Lower.MomentXyzKgM2
    UpperX, UpperY, UpperZ = Higher.MomentXyzKgM2
    Contact = (Upper.Maximum[0] - Upper.Minimum[0]) * (
        Upper.Maximum[1] - Upper.Minimum[1]
    )
    Value = BossMass(
        (*Lower.CentroidM[:2], CenterZ),
        Lower.VolumeM3 + Higher.VolumeM3,
        Lower.AreaM2 + Higher.AreaM2 - 2 * Contact,
        Mass,
        (LowerX + UpperX + Shift, LowerY + UpperY + Shift, LowerZ + UpperZ),
        (0.0, 0.0, 0.0),
    )
    if not all(map(isfinite, BossMassFields(Value))):
        raise ArchiveError("two-pad mass fields must be finite")
    return Value


# the geometry is fresh while the existing typed world-frame wrapper stays shared
def EncodeTwoPadMass(
    Generation: int,
    BodyCount: int,
    Base: PadBounds,
    Upper: PadBounds,
    DensityKgM3: float,
) -> bytes:
    RequireBossMassScope(Generation, BodyCount)
    Geometry = BossMassFields(CalcTwoPadMass(Base, Upper, DensityKgM3))
    return EncodeMassRecord(Geometry, KDefaultAccuracy)
