# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from interchange.enums.EnumGeometry import ConstraintKind, GeometryKind

# the recovered binary codes identify exact constraint semantics for supported roles
KLineRuleKinds = {
    2: "collinear",
    16: ConstraintKind.KParallel.value,
    32: ConstraintKind.KPerpendicular.value,
    2048: ConstraintKind.KEqual.value,
}

# planar circles and bounded arcs share tangent and radius based relation roles
KCircularKinds = frozenset({GeometryKind.KCircle, GeometryKind.KArcGeometry})

# point on object and tangent need a whole supported curve operand
KCurveKinds = KCircularKinds | {GeometryKind.KLine}


# a shape signature prevents shared codes from misrepresenting surface or spline relations
def GetGeomRuleKind(CodeValue: int, Kinds: tuple[GeometryKind | str, ...]) -> str:
    PointKind, LineKind = GeometryKind.KPoint, GeometryKind.KLine
    if CodeValue in (64, 128) and Kinds in ((LineKind,), (PointKind, PointKind)):
        return (
            ConstraintKind.KHorizontal.value
            if CodeValue == 64
            else ConstraintKind.KVertical.value
        )
    if CodeValue == 1:
        if Kinds == (PointKind, PointKind):
            return ConstraintKind.KCoincident.value
        if len(Kinds) == 2 and Kinds[0] == PointKind and Kinds[1] in KCurveKinds:
            return ConstraintKind.KPointOnObject.value
    if CodeValue in KLineRuleKinds and Kinds == (LineKind, LineKind):
        return KLineRuleKinds[CodeValue]
    if len(Kinds) == 2 and all(Value in KCircularKinds for Value in Kinds):
        if CodeValue == 4:
            return ConstraintKind.KConcentric.value
        if CodeValue == 2048:
            return ConstraintKind.KEqual.value
    if (
        CodeValue == 256
        and len(Kinds) == 2
        and all(Value in KCurveKinds for Value in Kinds)
        and Kinds != (LineKind, LineKind)
    ):
        return ConstraintKind.KTangent.value
    if CodeValue == 4096 and Kinds == (PointKind, LineKind):
        return ConstraintKind.KMidpoint.value
    if CodeValue == 1024 and Kinds == (PointKind, PointKind, LineKind):
        return ConstraintKind.KSymmetric.value
    raise ValueError(
        f"Unsupported Fusion geometric relation code {CodeValue} or operand roles"
    )
