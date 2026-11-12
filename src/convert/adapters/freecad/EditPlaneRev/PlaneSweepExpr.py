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
    TiltValue = f"abs(vdot({Normal}; {VectorExpr(AxisValue)}))"
    Offset = f"abs(vdot({PlaneName}.Placement.Base - {VectorExpr(AxisOrigin, ' mm')}; {Normal}))"
    Angle = f"atan2(-({Along}); {Across}) % (180 deg)"
    return f"{TiltValue} > 1e-9 ? 0 deg : ({Offset} > 1e-7 mm ? 0 deg : {Angle})"


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
