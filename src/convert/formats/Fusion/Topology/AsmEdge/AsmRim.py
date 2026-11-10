# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.Topology.AsmEdge.AsmFields import (
    IsAsmFlag,
    ReadAsmPtr,
    RequireAsm,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmNames import ReadCoedgeTag
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


# reciprocal coedges preserve their owner face and shared edge independently of coordinates
@MakeDataClass(frozen=True, slots=True)
class AsmUse:
    Identity: int
    FaceId: int
    EdgeId: int
    Partner: int
    Before: int
    Reverse: bool
    ProfileTag: int | None


# each planar source face owns exactly one reciprocal bounded coedge ring
def ReadAsmRim(
    Table: AsmTable, FaceId: int, LoopId: int, Maximum: int
) -> tuple[AsmUse, ...]:
    LoopValue = RequireAsm(Table, LoopId, "loop", 6)
    if ReadAsmPtr(LoopValue, 3) != -1 or ReadAsmPtr(LoopValue, 5) != FaceId:
        raise ValueError("Fusion ASM prism loop owner disagrees")
    First = ReadAsmPtr(LoopValue, 4)
    Current = First
    UseValues: list[AsmUse] = []
    Visited: set[int] = set()
    for _ in range(Maximum):
        Value = RequireAsm(Table, Current, "coedge", 11)
        if (
            Current in Visited
            or ReadAsmPtr(Value, 8) != LoopId
            or ReadAsmPtr(Value, 10) != -1
        ):
            raise ValueError("Fusion ASM prism coedge owner or trim disagrees")
        Visited.add(Current)
        UseValues.append(
            AsmUse(
                Current,
                FaceId,
                ReadAsmPtr(Value, 6),
                ReadAsmPtr(Value, 5),
                ReadAsmPtr(Value, 4),
                IsAsmFlag(Value, 7),
                ReadCoedgeTag(Table, Current, Value),
            )
        )
        Current = ReadAsmPtr(Value, 3)
        if Current == First:
            if len(UseValues) < 3 or any(
                UseValue.Before != UseValues[Index - 1].Identity
                for Index, UseValue in enumerate(UseValues)
            ):
                raise ValueError("Fusion ASM prism coedge ring is not reciprocal")
            return tuple(UseValues)
    raise ValueError("Fusion ASM prism coedge ring does not close")
