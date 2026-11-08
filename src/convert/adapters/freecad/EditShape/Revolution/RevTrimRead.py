# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from re import fullmatch as FullMatch

from convert.adapters.freecad.EditShape.CylinderRims import KAngleTolerance
from convert.adapters.freecad.EditShape.TrimBind import TrimBinding
from convert.adapters.freecad.EditShape.TrimGeometry import IsUnitPair, TrimCurve
from convert.geometry.Opencascade import DecodeFailure, ReadCount, Tokens


# known planar and rotational trims require only exact line and circle parameters
def ReadRevPcurves(Cursor: Tokens, Maximum: int) -> tuple[TrimCurve, ...]:
    Count = ReadCount(Cursor, b"Curve2ds", Maximum)
    Curves: list[TrimCurve] = []
    for _ in range(Count):
        Family = Cursor.ReadInteger(1, 2)
        Origin = (Cursor.ReadNumber(), Cursor.ReadNumber())
        Direction = (Cursor.ReadNumber(), Cursor.ReadNumber())
        if not IsUnitPair(Direction):
            raise DecodeFailure("invalid Revolution pcurve direction")
        if Family == 1:
            Curves.append(TrimCurve(Origin, Direction))
            continue
        SideValue = (Cursor.ReadNumber(), Cursor.ReadNumber())
        Radius = Cursor.ReadNumber()
        if (
            Radius <= 0.0
            or not IsUnitPair(SideValue)
            or abs(Direction[0] * SideValue[0] + Direction[1] * SideValue[1])
            > KAngleTolerance
        ):
            raise DecodeFailure("invalid Revolution pcurve circle")
        Curves.append(TrimCurve(Origin, Direction, SideValue, Radius))
    return tuple(Curves)


# exact edge representations retain trim continuity and parameter flags omitted by the model parser
def ReadRevTrims(
    Block: bytes, Curves: int, Pcurves: int, Surfaces: int, Locations: int
) -> tuple[TrimBinding, ...]:
    Cursor = Tokens(Block)
    _ = Cursor.ReadNumber()
    for Token in (b"1", b"1", b"0", b"1"):
        Cursor.ExpectToken(Token)
    _ = Cursor.ReadInteger(1, Curves)
    _ = Cursor.ReadInteger(0, Locations)
    _ = Cursor.ReadNumber()
    _ = Cursor.ReadNumber()
    Result: list[TrimBinding] = []
    while Family := Cursor.ReadInteger(0, 3):
        if Family == 1:
            raise DecodeFailure("multiple Revolution edge carriers")
        CurveIds = (Cursor.ReadInteger(1, Pcurves),)
        if Family == 3:
            CurveIds += (ReadRevSecond(Cursor, Pcurves),)
        Surface = Cursor.ReadInteger(1, Surfaces)
        Location = Cursor.ReadInteger(0, Locations)
        Lower, Upper = Cursor.ReadNumber(), Cursor.ReadNumber()
        Result.append(TrimBinding(CurveIds, Surface, Location, Lower, Upper))
    return tuple(Result)


# continuous native seam encodings allow both packed and separated curve indexes
def ReadRevSecond(Cursor: Tokens, Maximum: int) -> int:
    Match = FullMatch(rb"([1-9][0-9]*)(CN|C0)?", Cursor.TakeToken())
    if Match is None or (
        Match.group(2) is None and Cursor.TakeToken() not in {b"CN", b"C0"}
    ):
        raise DecodeFailure("unsupported Revolution seam continuity")
    Index = int(Match.group(1))
    if Index > Maximum:
        raise DecodeFailure("out of bounds Revolution seam pcurve")
    return Index
