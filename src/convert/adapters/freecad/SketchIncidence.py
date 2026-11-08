# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Mapping


# the target solver needs the stored incidence independently of the visible constraints
def GetIncidence(
    GeometryType: object, Attrs: Mapping[str, object]
) -> tuple[tuple[object, int], ...]:
    if GeometryType == "CircleGeometry":
        return ((Attrs.get("fusion.circle_native_center_id"), 3),)
    if GeometryType == "LineGeometry":
        PointRefs = Attrs.get("fusion.line_native_point_ids")
        Slots = (1, 2)
    elif GeometryType == "ArcGeometry":
        PointRefs = Attrs.get("fusion.arc_native_point_ids")
        Slots = (
            (3, 2, 1) if Attrs.get("fusion.arc_native_clockwise") is True else (3, 1, 2)
        )
    else:
        return ()
    Items = PointRefs.get("$tuple") if isinstance(PointRefs, Mapping) else None
    if not isinstance(Items, list) or len(Items) != len(Slots):
        return ()
    return tuple(zip(Items, Slots, strict=True))


# identical native point ids connect helper points to the specific curve slots they control
def FindPointLinks(
    Entities: list[dict[str, object]], Indices: Mapping[str, int]
) -> tuple[tuple[tuple[int, int], tuple[int, int]], ...]:
    Points = {
        EntityId: Indices[EntityId]
        for Entity in Entities
        if isinstance(EntityId := Entity.get("id"), str)
        and EntityId in Indices
        and isinstance(Geometry := Entity.get("geometry"), Mapping)
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
            or not isinstance(Geometry, Mapping)
        ):
            continue
        for NativeId, PointSlot in GetIncidence(Geometry.get("$type"), Attrs):
            if type(NativeId) is not int:
                continue
            PointId = f"fusion-sketch-entity-{NativeId}"
            if PointId in Points:
                Links.append(((Indices[EntityId], PointSlot), (Points[PointId], 1)))
    return tuple(Links)
