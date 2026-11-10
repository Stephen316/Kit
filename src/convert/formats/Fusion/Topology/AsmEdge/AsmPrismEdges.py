# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.Topology.AsmEdge.AsmFields import (
    IsAsmFlag,
    ReadAsmPtr,
    RequireAsm,
)
from convert.formats.Fusion.Topology.AsmEdge.AsmPrism import AsmPrism
from convert.formats.Fusion.Topology.AsmEdge.AsmRim import AsmUse
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import AsmTable


# source edge incidence carries ordered native vertices and the optional exact profile tag
@MakeDataClass(frozen=True, slots=True)
class AsmPrismEdge:
    Identity: int
    Vertices: tuple[int, int]
    Faces: frozenset[int]
    ProfileTag: int | None


# each edge is a bounded straight connection between two reciprocal face uses
def ReadAsmEdge(
    Table: AsmTable, Identity: int, UseValues: list[AsmUse]
) -> AsmPrismEdge:
    Value = RequireAsm(Table, Identity, "edge", 11)
    Start, Finish = ReadAsmPtr(Value, 3), ReadAsmPtr(Value, 5)
    if len(UseValues) != 2:
        raise ValueError("Fusion ASM source edge is missing its pair of uses")
    First, Second = UseValues
    if (
        Start == Finish
        or IsAsmFlag(Value, 9)
        or ReadAsmPtr(Value, 7) not in (First.Identity, Second.Identity)
        or First.Partner != Second.Identity
        or Second.Partner != First.Identity
        or First.FaceId == Second.FaceId
        or First.Reverse == Second.Reverse
        or First.ProfileTag != Second.ProfileTag
    ):
        raise ValueError("Fusion ASM source edge coedge ownership disagrees")
    _ = RequireAsm(Table, ReadAsmPtr(Value, 8), "straight-curve")
    return AsmPrismEdge(
        Identity,
        (Start, Finish),
        frozenset((First.FaceId, Second.FaceId)),
        First.ProfileTag,
    )


# identical vertex identities must connect each ordered face ring
def ReadAsmEdges(
    Table: AsmTable, Prism: AsmPrism, Sides: int
) -> dict[int, AsmPrismEdge]:
    ByEdge: dict[int, list[AsmUse]] = {}
    UseIds: set[int] = set()
    for RingValue in Prism.Rings.values():
        for UseValue in RingValue:
            if UseValue.Identity in UseIds:
                raise ValueError("Fusion ASM coedge appears in multiple face rings")
            UseIds.add(UseValue.Identity)
            ByEdge.setdefault(UseValue.EdgeId, []).append(UseValue)
    if len(ByEdge) != 3 * Sides or len(UseIds) != 6 * Sides:
        raise ValueError("Fusion ASM source edge inventory is not a prism")
    Edges = {
        Identity: ReadAsmEdge(Table, Identity, UseValues)
        for Identity, UseValues in ByEdge.items()
    }
    for RingValue in Prism.Rings.values():
        Ordered = tuple(
            (
                Edges[UseValue.EdgeId].Vertices[::-1]
                if UseValue.Reverse
                else Edges[UseValue.EdgeId].Vertices
            )
            for UseValue in RingValue
        )
        if any(
            First[1] != Second[0]
            for First, Second in zip(Ordered, Ordered[1:] + Ordered[:1], strict=True)
        ):
            raise ValueError("Fusion ASM source face vertex ring does not close")
    return Edges
