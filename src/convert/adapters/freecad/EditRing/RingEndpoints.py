# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from convert.adapters.base.WriteValidate import IsObjectTuple
from interchange.geometry.models.Sketch import SketchEntity


# native point identifiers establish incidence independently of coincident coordinates
def ReadRingEnds(Entity: SketchEntity) -> tuple[str, str]:
    PointIds = Entity.attributes.get("fusion.line_native_point_ids")
    if (
        not IsObjectTuple(PointIds)
        or len(PointIds) != 2
        or any(type(Value) is not int or Value <= 0 for Value in PointIds)
        or PointIds[0] == PointIds[1]
    ):
        raise ValueError("FreeCAD editable ring has an invalid native endpoint binding")
    return f"fusion-sketch-entity-{PointIds[0]}", f"fusion-sketch-entity-{PointIds[1]}"


# a whole ring visits each native vertex once before returning to its first point
def CheckRingEnds(Endpoints: tuple[tuple[str, str], ...]) -> frozenset[str]:
    Start, Current = Endpoints[0]
    Visited = {Start, Current}
    for Index, (First, Second) in enumerate(Endpoints[1:], 1):
        if Current == First:
            Current = Second
        elif Current == Second:
            Current = First
        else:
            raise ValueError("FreeCAD editable ring native endpoints do not connect")
        if Index == len(Endpoints) - 1:
            if Current != Start:
                raise ValueError("FreeCAD editable ring native endpoints do not close")
        elif Current in Visited:
            raise ValueError("FreeCAD editable ring repeats a native vertex")
        Visited.add(Current)
    return frozenset(Visited)
