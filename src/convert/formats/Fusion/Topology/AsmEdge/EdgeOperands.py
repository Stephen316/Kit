# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import dataclass as MakeDataClass
from struct import unpack_from as UnpackFrom

from convert.formats.Fusion.Topology.AsmEdge.AsmNames import KNameTerms


# ordered endpoint triples distinguish the authored source edge direction
@MakeDataClass(frozen=True, slots=True)
class EdgeOperands:
    Faces: tuple[KNameTerms, KNameTerms]
    Endpoints: tuple[tuple[KNameTerms, ...], tuple[KNameTerms, ...]]


# every operand index is a framed reference into the same exact name table
def ReadOperandRefs(
    Payload: bytes, Offset: int, Count: int, Terms: tuple[KNameTerms, ...]
) -> tuple[KNameTerms, ...]:
    Indices = []
    for Index in range(Count):
        Entry, Sentinel = UnpackFrom("<2i", Payload, Offset + 8 * Index)
        if Sentinel != -1 or not 0 <= Entry < len(Terms):
            raise ValueError("Invalid Fusion edge recipe name reference")
        Indices.append(Entry)
    if len(set(Indices)) != Count:
        raise ValueError("Duplicate Fusion edge recipe operand")
    return tuple(Terms[Index] for Index in Indices)


# the bounded straight selector names two faces and both three face endpoints
def ReadEdgeRecipe(Terms: tuple[KNameTerms, ...], Payload: bytes) -> EdgeOperands:
    if (
        len(Payload) != 116
        or len(Terms) != 4
        or len(set(Terms)) != 4
        or UnpackFrom("<2iI", Payload) != (-1, -1, 2)
        or UnpackFrom("<I", Payload, 28) != (2,)
        or Payload[-4:] not in (bytes(4), b"\xff" * 4)
    ):
        raise ValueError("Unsupported Fusion straight edge recipe")
    First, Second = ReadOperandRefs(Payload, 12, 2, Terms)
    EndValues = []
    for Offset in (32, 72):
        if UnpackFrom("<iI", Payload, Offset) != (-1, 3) or Payload[
            Offset + 32 : Offset + 40
        ] != bytes(8):
            raise ValueError("Invalid Fusion edge recipe endpoint framing")
        EndValues.append(ReadOperandRefs(Payload, Offset + 8, 3, Terms))
    Start, Finish = EndValues
    PairNames = {First, Second}
    if set(Start) == set(Finish) or any(
        not PairNames <= set(Value) for Value in EndValues
    ):
        raise ValueError("Fusion edge recipe endpoint incidence disagrees")
    return EdgeOperands((First, Second), (Start, Finish))
