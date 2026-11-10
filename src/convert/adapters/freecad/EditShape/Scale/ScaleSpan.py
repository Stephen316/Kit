# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from dataclasses import dataclass as MakeDataClass
from math import isfinite as IsFinite

from convert.geometry.Opencascade import DecodeFailure, Tokens


# native degree one carriers need exact knot domains for later parameter correspondence
@MakeDataClass(frozen=True, slots=True)
class ScaleSpan:
    Start: tuple[float, ...]
    EndPoint: tuple[float, ...]
    Domain: tuple[float, float]


# clamped single spans make the knot domain the full affine interpolation interval
def ReadScaleDomain(Cursor: Tokens) -> tuple[float, float]:
    Lower = Cursor.ReadNumber()
    Cursor.ExpectToken(b"2")
    Upper = Cursor.ReadNumber()
    Cursor.ExpectToken(b"2")
    if Lower >= Upper or not IsFinite(Upper - Lower):
        raise DecodeFailure("Scale spline knot interval must increase")
    return Lower, Upper


# bounded native edges and trims can be qualified without a general spline evaluator
def ReadScaleSpan(Cursor: Tokens, Dimension: int) -> ScaleSpan:
    Cursor.ExpectToken(b"8")
    Bounds = (Cursor.ReadNumber(), Cursor.ReadNumber())
    for Token in (b"7", b"0", b"0", b"1", b"2", b"2"):
        Cursor.ExpectToken(Token)
    Start = tuple(Cursor.ReadNumber() for _ in range(Dimension))
    EndPoint = tuple(Cursor.ReadNumber() for _ in range(Dimension))
    Domain = ReadScaleDomain(Cursor)
    if Bounds != Domain or Start == EndPoint:
        raise DecodeFailure("invalid bounded Scale spline curve")
    return ScaleSpan(Start, EndPoint, Domain)
