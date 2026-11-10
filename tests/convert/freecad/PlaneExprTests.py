# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

import pytest as Pytest

from convert.adapters.freecad.EditRead.PlaneRev.ExprMatch import IsSamePlaneExpr


# resaving a native expression may alter its formatting without altering its meaning
@Pytest.mark.parametrize(
    ("Expected", "Actual"),
    (
        (
            "atan2(-(vdot((Plane.Placement.Rotation * vector(0; 0; 1)); "
            + "vector(0; 0; 1))); 1) % (180 deg)",
            "atan2(-vdot(Plane.Placement.Rotation * vector(0; 0; 1); "
            + "vector(0; 0; 1)); 1) % 180 deg",
        ),
        (
            "placement(vector(12.125000000000002 mm; -0 mm; 0 mm); "
            + "rotation(vector(0; 1; 0); 89.999999999999986 deg))",
            "placement(vector(12.125 mm; -0 mm; 0 mm); "
            + "rotation(vector(0; 1; 0); 90 deg))",
        ),
        (
            "min(1 deg; 2 deg) <= 0.00000006 deg ? 0 deg : (1e-9 > 1e-7 ? 0 deg : 1 deg)",
            " min(1.0 deg; 2 deg) <= 6e-08 deg ? 0 deg : 1e-09 > 1e-07 ? 0 deg : 1 deg ",
        ),
        (
            "Parameters.fusion_parameter_242 / 2 * (3 + 4)",
            "(Parameters.fusion_parameter_242 / 2) * (3 + 4)",
        ),
    ),
)
def CheckSavedExpr(Expected: str, Actual: str) -> None:
    assert IsSamePlaneExpr(Expected, Actual)


# structural checks must reject altered controls even if some values could coincide
@Pytest.mark.parametrize(
    ("Expected", "Actual"),
    (
        ("Parameters.depth + 2 deg", "Parameters.other + 2 deg"),
        ("Plane.Placement.Rotation", "Plane.Placement.Base"),
        ("1 mm + 2 mm", "2 mm + 1 mm"),
        ("1 mm + 2 mm", "1 mm - 2 mm"),
        ("1 mm + 2 mm", "3 mm"),
        ("1 * (2 + 3)", "1 * 2 + 3"),
        ("1 / (2 * 3)", "1 / 2 * 3"),
        ("-(1 + 2)", "-1 + 2"),
        ("-(1 + 2)", "+(1 + 2)"),
        ("1 < 2 ? 0 deg : 3 deg", "1 <= 2 ? 0 deg : 3 deg"),
        ("1 < 2 ? 0 deg : 3 deg", "1 < 2 ? 3 deg : 0 deg"),
        ("1 < 2 ? 0 deg : 3 deg", "(1 < 2 ? 0 deg : 3 deg) ? 1 deg : 2 deg"),
        ("atan2(1; 2)", "atan2(2; 1)"),
        ("atan2(1; 2)", "min(1; 2)"),
        ("1 mm", "1 deg"),
        ("1 mm", "1"),
        ("12.125000000000002 mm", "12.1250000000001 mm"),
        ("12.125 mm", "12.125000000000002 mm"),
        ("0 deg", "1e-308 deg"),
    ),
)
def CheckExprChange(Expected: str, Actual: str) -> None:
    assert not IsSamePlaneExpr(Expected, Actual)


# even identical inputs must be parsed within the observed native syntax and size limits
@Pytest.mark.parametrize(
    "Expression",
    (
        "",
        "1 +",
        "(1 + 2",
        "1 < 2 ? 3",
        "abs(1; 2)",
        "pow(1; 2)",
        "atan2(1, 2)",
        "1 + 2 trailing",
        "1 deg\x00",
        "1e99999",
        "1e-99999",
        "0e" + "1" * 70,
        "(" * 80 + "1" + ")" * 80,
        "-" * 80 + "1",
        "+".join(["1"] * 2500),
        "a" * 66000,
    ),
)
def CheckInvalid(Expression: str) -> None:
    assert not IsSamePlaneExpr(Expression, Expression)


# flat comparison keeps a valid long chain independent of recursion limits
def CheckLongChain() -> None:
    Expression = "+".join(["1"] * 1500)
    assert IsSamePlaneExpr(Expression, f"({Expression})")


# long native object names can recur across a generated two plane limit
def CheckLongNames() -> None:
    First = "Plane" + "A" * 1024 + ".Placement.Rotation"
    Other = "Plane" + "B" * 1024 + ".Placement.Rotation"
    Expression = " + ".join([First, Other] * 16)
    assert IsSamePlaneExpr(Expression, f"({Expression})")
