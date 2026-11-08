# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import dataclass as MakeDataClass
from re import fullmatch as FullMatch

from convert.geometry.Opencascade import DecodeFailure, Tokens


# both native seam encodings bind two curves to one cylindrical surface
@MakeDataClass(frozen=True, slots=True)
class TrimBinding:
    CurveIds: tuple[int, ...]
    SurfaceId: int
    Placement: int
    Lower: float
    Upper: float


# native saves permit both packed and separated seam continuity tokens
def ReadSecondTrim(Cursor: Tokens, CurveCount: int) -> int:
    Token = Cursor.TakeToken()
    Match = FullMatch(rb"([1-9][0-9]*)(?:CN)?", Token)
    if Match is None:
        raise DecodeFailure("unsupported extrusion seam continuity")
    if Token == Match.group(1):
        Cursor.ExpectToken(b"CN")
    Index = int(Match.group(1))
    if Index > CurveCount:
        raise DecodeFailure("extrusion seam curve is out of bounds")
    return Index


# edge pcurves must retain their surface bindings after parsing three dimensional topology
def ReadTrimBinds(
    RecordData: bytes, CurveCount: int, SurfaceCount: int, PlaceCount: int
) -> tuple[TrimBinding, ...]:
    Cursor = Tokens(RecordData)
    _ = Cursor.ReadNumber()
    for _ in range(3):
        _ = Cursor.ReadInteger(0, 1)
    Result: list[TrimBinding] = []
    while KindValue := Cursor.ReadInteger(0, 3):
        if KindValue == 1:
            _ = Cursor.ReadInteger(1, 3)
            _ = Cursor.ReadInteger(0, PlaceCount)
            _ = Cursor.ReadNumber()
            _ = Cursor.ReadNumber()
            continue
        CurveIds = (Cursor.ReadInteger(1, CurveCount),)
        if KindValue == 3:
            CurveIds += (ReadSecondTrim(Cursor, CurveCount),)
        Result.append(
            TrimBinding(
                CurveIds,
                Cursor.ReadInteger(1, SurfaceCount),
                Cursor.ReadInteger(0, PlaceCount),
                Cursor.ReadNumber(),
                Cursor.ReadNumber(),
            )
        )
    return tuple(Result)
