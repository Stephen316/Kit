# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.base.WriteValidate import IsObjectMap


# the target solver needs the stored incidence independently of the visible constraints
def GetIncidence(
    GeometryType: object, Attrs: Mapping[str, object]
) -> tuple[tuple[object, int], ...]:
    if GeometryType == "CircleGeometry":
        return ((Attrs.get("fusion.circle_native_center_id"), 3),)
    if GeometryType == "LineGeometry":
        PointRefs = Attrs.get("fusion.line_native_point_ids")
        Slots: tuple[int, ...] = (1, 2)
    elif GeometryType == "ArcGeometry":
        PointRefs = Attrs.get("fusion.arc_native_point_ids")
        Slots = (
            (3, 2, 1) if Attrs.get("fusion.arc_native_clockwise") is True else (3, 1, 2)
        )
    else:
        return ()
    Items = PointRefs.get("$tuple") if IsObjectMap(PointRefs) else None
    if not isinstance(Items, list) or len(CastValue(list[object], Items)) != len(Slots):
        return ()
    return tuple(zip(CastValue(list[object], Items), Slots, strict=True))


# identical native point ids connect helper points to the specific curve slots they control
def FindPointLinks(
    Entities: list[dict[str, object]], Indices: Mapping[str, int]
) -> tuple[tuple[tuple[int, int], tuple[int, int]], ...]:
    Points = {
        EntityId: Indices[EntityId]
        for Entity in Entities
        if isinstance(EntityId := Entity.get("id"), str)
        and EntityId in Indices
        and IsObjectMap(Geometry := Entity.get("geometry"))
        and Geometry.get("$type") == "PointGeometry"
    }
    Links: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for Entity in Entities:
        EntityId, Attrs = Entity.get("id"), Entity.get("attributes")
        Geometry = Entity.get("geometry")
        if (
            not isinstance(EntityId, str)
            or EntityId not in Indices
            or not isinstance(Attrs, Mapping)
            or not IsObjectMap(Geometry)
        ):
            continue
        for NativeId, PointSlot in GetIncidence(
            Geometry.get("$type"), CastValue(Mapping[str, object], Attrs)
        ):
            if type(NativeId) is not int:
                continue
            PointId = f"fusion-sketch-entity-{NativeId}"
            if PointId in Points:
                Links.append(((Indices[EntityId], PointSlot), (Points[PointId], 1)))
    return tuple(Links)
