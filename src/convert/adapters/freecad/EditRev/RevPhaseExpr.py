# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Literal


# averaging local endpoints before applying translation preserves the saved expression order
def RevMeanExpr(
    Profile: str,
    ProfileLines: tuple[int, ...],
    MeanStyle: Literal["world", "legacy", "saved"] = "world",
) -> str:
    Corners = " + ".join(
        f"{Profile}.Geometry[{Index}].{Endpoint}"
        for Index in ProfileLines
        for Endpoint in ("StartPoint", "EndPoint")
    )
    Count = 2 * len(ProfileLines)
    Pose = f"{Profile}.Placement"
    if MeanStyle == "legacy":
        return f"({Pose} * (({Corners}) / {Count}))"
    if MeanStyle == "saved":
        return f"(({Pose} * ({Corners})) / {Count})"
    return f"({Pose}.Base + ({Pose}.Rotation * ({Corners})) / {Count})"


# both linked axis families use the occupied coplanar half plane for positive sweep
def RevPhaseExpr(
    Along: str, Start: str, Point: str, Profile: str, Reference: str
) -> str:
    Normal = f"({Profile}.Placement.Rotation * vector(0; 0; 1))"
    Radial = f"({Point} - {Start})"
    Tilt = f"abs(vdot({Along}; {Normal}))"
    Offset = f"abs(vdot({Radial}; {Normal}))"
    Sense = f"vdot(vcross({Along}; {Radial}); {Normal})"
    Signed = f"{Sense} > 0 ? {Reference} : ({Sense} < 0 ? -{Reference} : 0 deg)"
    return f"{Tilt} > 1e-8 ? 0 deg : ({Offset} > 1e-8 ? 0 deg : ({Signed}))"
