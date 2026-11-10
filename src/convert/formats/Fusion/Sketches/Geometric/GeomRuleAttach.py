# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from dataclasses import replace as Replace

from convert.formats.Fusion.ParamProjection import ParamOrigin as RecordOrigin
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Sketches.Geometric.GeomRuleKinds import GetGeomRuleKind
from convert.formats.Fusion.Sketches.Geometric.GeomRuleRecord import (
    KGeomRuleGuid,
    ReadGeomRule,
)
from interchange.core.Common import FreezeMapping
from interchange.enums.EnumGeometry import ConstraintKind, GeometryKind
from interchange.geometry.models.Sketch import (
    ConstraintRef,
    SketchEntity,
    SketchRelation,
)


# planar solver roles must follow the repeated native arguments and owning sketch roster
def AttachGeomRule(
    BulkData: bytes,
    SpanValue: RecordSpan,
    RootSpan: RecordSpan,
    Entities: dict[int, SketchEntity],
) -> SketchRelation:
    Start = SpanValue.PayloadOffset + 4
    if (
        not SpanValue.IsPrimary
        or SpanValue.ClassGuid != KGeomRuleGuid
        or not 0 <= Start <= SpanValue.EndOffset <= len(BulkData)
    ):
        raise ValueError("Unsupported Fusion geometric relation class")
    Native = ReadGeomRule(BulkData[Start : SpanValue.EndOffset])
    if Native.OwnerId != RootSpan.ObjectId or not all(
        Identity in Entities for Identity in Native.Arguments
    ):
        raise ValueError("Fusion geometric relation owner or entity scope disagrees")
    Targets = tuple(Entities[Identity] for Identity in Native.Arguments)
    KindValue = GetGeomRuleKind(
        Native.CodeValue, tuple(Entity.kind for Entity in Targets)
    )
    Reordered = KindValue in (ConstraintKind.KMidpoint, ConstraintKind.KPointOnObject)
    Expected = Native.Arguments[::-1] if Reordered else Native.Arguments
    if Native.Dependencies != Expected:
        raise ValueError("Fusion geometric relation argument roles disagree")
    Origin = RecordOrigin(SpanValue)
    return SketchRelation(
        id=f"fusion-sketch-relation-{SpanValue.ObjectId}",
        kind=KindValue,
        references=tuple(
            ConstraintRef(
                Entity.id, "start" if Entity.kind == GeometryKind.KPoint else ""
            )
            for Entity in Targets
        ),
        provenance=Replace(Origin, spans=Origin.spans + RecordOrigin(RootSpan).spans),
        attributes=FreezeMapping(
            {
                "fusion.native_constraint_code": Native.CodeValue,
                "fusion.constraint_sketch_id": Native.OwnerId,
                "fusion.constraint_dependency_ids": Native.Dependencies,
                "fusion.constraint_argument_ids": Native.Arguments,
            }
        ),
    )
