# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.adapters.freecad.EditPlaneRev.PlanePoseExpr import (
    PlanePoseExpr,
    RotationExpr,
)
from interchange.features.FeatureBoundPlane import BoundConstructionPlane


# a whole placement expression preserves the reference basis and the signed live control
def DatumPoseExpr(
    Definition: BoundConstructionPlane,
    ZeroQuat: tuple[float, float, float, float],
    ParamRef: str,
) -> str:
    Frame = Definition.ReferenceFrame
    if Definition.Method == "angle":
        return PlanePoseExpr(
            Frame.origin, Frame.x_axis, Frame.origin, ZeroQuat, ParamRef
        )
    Origin = Frame.origin
    Normal = Frame.z_axis
    Coordinates = "; ".join(
        f"{Base:.17g} mm + ({Axis:.17g}) * {ParamRef}"
        for Base, Axis in (
            (Origin.x, Normal.x),
            (Origin.y, Normal.y),
            (Origin.z, Normal.z),
        )
    )
    return f"placement(vector({Coordinates}); {RotationExpr(ZeroQuat)})"
