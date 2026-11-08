# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from math import cos as Cosine, sin as SinValue

from convert.adapters.freecad.EditableRev import EditRevolve
from convert.adapters.freecad.EditRead.EditPlacement import CheckEditFrame
from convert.adapters.freecad.Native import NativeObject
from convert.geometry.Revolve.SweepVector import CrossVector, DotVector, OffsetVector
from interchange.geometry.models.Transform import (
    KOriginZero,
    KTransformIdentity,
    Transform,
)
from interchange.geometry.models.VectorSpace import SpaceVector


# the fixed axis rotates the centered sweep without moving its origin
def RotateRevAxis(
    Direction: SpaceVector, Basis: SpaceVector, Angle: float
) -> SpaceVector:
    CosValue = Cosine(Angle)
    SinTerm = OffsetVector(KOriginZero, CrossVector(Direction, Basis), SinValue(Angle))
    Scale = DotVector(Direction, Basis) * (1.0 - CosValue)
    return OffsetVector(OffsetVector(SinTerm, Basis, CosValue), Direction, Scale)


# generated seed geometry is already world placed while a saved sweep has the evaluated pose
def CheckRevPose(
    Native: NativeObject,
    PlanValue: EditRevolve,
    Along: float,
    Against: float | None,
    IsSeed: bool,
) -> None:
    Identity = KTransformIdentity
    if IsSeed:
        CheckEditFrame(Native, "Placement", Identity, Optional=True)
        return
    Expected = Identity
    if Against is not None and PlanValue.AngleScale == 1.0:
        Midpoint = (Along - Against) / 2.0
        Direction = PlanValue.AxisDirection
        Expected = Transform(
            origin=KOriginZero,
            x_axis=RotateRevAxis(Direction, Identity.x_axis, Midpoint),
            y_axis=RotateRevAxis(Direction, Identity.y_axis, Midpoint),
            z_axis=RotateRevAxis(Direction, Identity.z_axis, Midpoint),
        )
    CheckEditFrame(Native, "Placement", Expected)
