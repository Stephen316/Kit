# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


# native positive sweep follows the half plane currently occupied by the profile
def AxisAngleExpr(
    AxisSketch: str,
    AxisIndex: int,
    Profile: str,
    ProfileLines: tuple[int, ...],
    Reference: str,
) -> str:
    Guide = f"{AxisSketch}.Geometry[{AxisIndex}]"
    Start = f"({AxisSketch}.Placement * {Guide}.StartPoint)"
    EndValue = f"({AxisSketch}.Placement * {Guide}.EndPoint)"
    Corners = " + ".join(
        f"{Profile}.Geometry[{Index}].{Endpoint}"
        for Index in ProfileLines
        for Endpoint in ("StartPoint", "EndPoint")
    )
    Point = f"({Profile}.Placement * (({Corners}) / {2 * len(ProfileLines)}))"
    Normal = f"({Profile}.Placement.Rotation * vector(0; 0; 1))"
    Along = f"({EndValue} - {Start})"
    Radial = f"({Point} - {Start})"
    Tilt = f"abs(vdot({Along}; {Normal}))"
    Offset = f"abs(vdot({Radial}; {Normal}))"
    Sense = f"vdot(vcross({Along}; {Radial}); {Normal})"
    Signed = f"{Sense} > 0 ? {Reference} : ({Sense} < 0 ? -{Reference} : 0 deg)"
    return f"{Tilt} > 1e-8 ? 0 deg : ({Offset} > 1e-8 ? 0 deg : ({Signed}))"
