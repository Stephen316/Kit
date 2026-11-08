# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.freecad.EditPlaneRev.PlanePoseExpr import VectorExpr
from convert.geometry.Revolve.SweepVector import CrossVector
from interchange.geometry.models.VectorSpace import SpaceVector

# a zero sweep makes coincident planes fail instead of generating an unrelated solid
KPlaneGuard = "0.00000006 deg"


# either orientation of a plane normal must yield the same root in one half turn
def TargetLimitExpr(
    PlaneName: str,
    AxisOrigin: SpaceVector,
    AxisValue: SpaceVector,
    Tangent: SpaceVector,
) -> str:
    Radial = CrossVector(Tangent, AxisValue)
    Normal = f"({PlaneName}.Placement.Rotation * vector(0; 0; 1))"
    Along = f"vdot({Normal}; {VectorExpr(Radial)})"
    Across = f"vdot({Normal}; {VectorExpr(Tangent)})"
    Tilt = f"abs(vdot({Normal}; {VectorExpr(AxisValue)}))"
    Offset = (
        f"abs(vdot({PlaneName}.Placement.Base - {VectorExpr(AxisOrigin)}; {Normal}))"
    )
    Angle = f"atan2(-({Along}); {Across}) % (180 deg)"
    return f"{Tilt} > 1e-9 ? 0 deg : ({Offset} > 1e-7 ? 0 deg : {Angle})"


# fusion uses the interval between consecutive lifted plane roots beyond the sketch
def PlaneSweepExpr(
    PlaneNames: tuple[str, ...],
    AxisOrigin: SpaceVector,
    AxisValue: SpaceVector,
    Tangent: SpaceVector,
) -> list[tuple[str, str]]:
    Limits = tuple(
        f"({TargetLimitExpr(NameValue, AxisOrigin, AxisValue, Tangent)})"
        for NameValue in PlaneNames
    )
    Clearances = [f"{Value}; 180 deg - {Value}" for Value in Limits]
    if len(Limits) == 1:
        Guard = f"min({Clearances[0]}) <= {KPlaneGuard}"
        return [("Angle", f"{Guard} ? 0 deg : {Limits[0]}")]
    First, Second = Limits
    Difference = f"abs({First} - {Second})"
    Clearances.append(Difference)
    Guard = f"min({'; '.join(Clearances)}) <= {KPlaneGuard}"
    Center = f"({First} + {Second} + 180 deg) / 2"
    Rotation = f"rotation({VectorExpr(AxisValue)}; {Center})"
    return [
        ("Angle", f"{Guard} ? 0 deg : 180 deg - {Difference}"),
        ("Placement", f"placement({VectorExpr(AxisOrigin, ' mm')}; {Rotation})"),
    ]
