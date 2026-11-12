from dataclasses import dataclass as MakeDataClass

from interchange.enums.EnumGeometry import ConstraintKind, GeometryKind

# observed native classes keep dimension codes from being interpreted in other layouts
KLinearDimension = "8C780195-72C0-4a56-A911-E43AB14357F2"

# angle flags have a different layout from linear distance controls
KAngleDimension = "6EEAFDE5-59C4-424D-8EBE-77CDBC562017"

# radial dimensions use a dedicated class and value annotation prefix
KRadiusDimension = "8EDAC24D-35D4-4591-B8E7-B3EA081C9DF0"

# diameters retain their native kind independently of radial support geometry
KDiaDimension = "664AD49F-207F-4CD5-8555-DD269E9F09EA"

# tangent side selection needs a separate proof before it can drive a relation
KTangentDimension = "A9E23439-6F4F-4ED3-A610-319F0AFABEED"

# explicit classes let the projection report known unsupported dimension variants
KDimensionClasses = frozenset(
    {
        KLinearDimension,
        KAngleDimension,
        KRadiusDimension,
        KDiaDimension,
        KTangentDimension,
    }
)


# paired native controls qualify each exact source and geometric operand combination
@MakeDataClass(frozen=True, slots=True)
class DimensionSpec:
    KindValue: ConstraintKind
    ClassGuid: str
    Targets: tuple[GeometryKind, ...]
    RolePrefix: str
    FlagOffset: int
    TailSize: int
    Symbol: str = ""


# both point targets are explicit native operands on every basic linear dimension
KPointPair = (GeometryKind.KPoint, GeometryKind.KPoint)

# an angular dimension uses the ordered directions of two complete lines
KLinePair = (GeometryKind.KLine, GeometryKind.KLine)

# the proven radial and diameter reference flag layouts use complete circles
KCircleTarget = (GeometryKind.KCircle,)

# the code table qualifies only dimension variants with proven geometric semantics
KDimensionSpecs = {
    0x4000: DimensionSpec(
        ConstraintKind.KDistance, KLinearDimension, KPointPair, "Linear", 129, 52
    ),
    0x400000: DimensionSpec(
        ConstraintKind.KDistanceX, KLinearDimension, KPointPair, "Linear", 129, 52
    ),
    0x800000: DimensionSpec(
        ConstraintKind.KDistanceY, KLinearDimension, KPointPair, "Linear", 129, 52
    ),
    0x8000: DimensionSpec(
        ConstraintKind.KAngle, KAngleDimension, KLinePair, "Angular", 146, 32
    ),
    0x20000: DimensionSpec(
        ConstraintKind.KRadius, KRadiusDimension, KCircleTarget, "Radial", 153, 32, "R"
    ),
    0x10000: DimensionSpec(
        ConstraintKind.KDiameter, KDiaDimension, KCircleTarget, "Diameter", 153, 32, "Ø"
    ),
}
