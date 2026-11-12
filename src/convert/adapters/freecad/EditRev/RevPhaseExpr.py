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
    PoseValue = f"{Profile}.Placement"
    if MeanStyle == "legacy":
        return f"({PoseValue} * (({Corners}) / {Count}))"
    if MeanStyle == "saved":
        return f"(({PoseValue} * ({Corners})) / {Count})"
    return f"({PoseValue}.Base + ({PoseValue}.Rotation * ({Corners})) / {Count})"


# both linked axis families use the occupied coplanar half plane for positive sweep
def RevPhaseExpr(
    Along: str, Start: str, Point: str, Profile: str, Reference: str
) -> str:
    Normal = f"({Profile}.Placement.Rotation * vector(0; 0; 1))"
    Radial = f"({Point} - {Start})"
    TiltValue = f"abs(vdot({Along}; {Normal}))"
    Offset = f"abs(vdot({Radial}; {Normal}))"
    Sense = f"vdot(vcross({Along}; {Radial}); {Normal})"
    Signed = f"{Sense} > 0 ? {Reference} : ({Sense} < 0 ? -{Reference} : 0 deg)"
    return f"{TiltValue} > 1e-8 ? 0 deg : ({Offset} > 1e-8 ? 0 deg : ({Signed}))"
