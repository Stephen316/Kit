# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as Replace

from convert.formats.Fusion.ParamProjection import ParamOrigin
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Sketches.Dimensional.DimBinding import ReadDimParam
from convert.formats.Fusion.Sketches.Dimensional.DimControls import ReadDimControls
from convert.formats.Fusion.Sketches.Dimensional.DimMeasure import CheckDimMeasure
from convert.formats.Fusion.Sketches.Dimensional.DimRecord import (
    DimRecordBody,
    ReadDimRecord,
)
from convert.formats.Fusion.Sketches.Dimensional.DimScope import DimensionScope
from convert.formats.Fusion.Sketches.Dimensional.DimSpec import (
    KDimensionClasses,
    KDimensionSpecs,
)
from interchange.core.Common import FreezeMapping
from interchange.enums.EnumGeometry import ConstraintKind, GeometryKind
from interchange.geometry.models.Sketch import ConstraintRef, SketchRelation


# projection preserves explicit native point identities and never chooses nearby endpoints
def AttachDimRule(
    BulkData: bytes,
    SpanValue: RecordSpan,
    Owners: dict[int, RecordSpan],
    Scope: DimensionScope,
) -> SketchRelation:
    if SpanValue.ClassGuid not in KDimensionClasses:
        raise ValueError("Unsupported Fusion sketch dimension class")
    BodyValue = DimRecordBody(BulkData, SpanValue)
    Native = ReadDimRecord(BodyValue)
    SpecValue = KDimensionSpecs.get(Native.Code)
    if SpecValue is None or SpecValue.ClassGuid != SpanValue.ClassGuid:
        raise ValueError(f"Unsupported Fusion sketch dimension code {Native.Code:#x}")
    if any(Identity not in Scope.Entities for Identity in Native.TargetIds):
        raise ValueError("Fusion dimension operands do not resolve in their sketch")
    Entities = tuple(Scope.Entities[Identity] for Identity in Native.TargetIds)
    if tuple(Value.kind for Value in Entities) != SpecValue.Targets:
        raise ValueError("Unsupported Fusion sketch dimension operand types")
    ParamMatches = Scope.Bindings.get(Native.BindingId, ())
    if len(ParamMatches) != 1:
        raise ValueError(
            "Missing or ambiguous Fusion sketch dimension parameter binding"
        )
    ParamValue = ParamMatches[0]
    NativeParam, ParamSpan, BindingSpan = ReadDimParam(
        BulkData, Owners, ParamValue, Native.BindingId, Scope.FeatureId, SpecValue
    )
    Driving, TextPosition = ReadDimControls(
        BodyValue, Native, SpecValue, NativeParam.Formula
    )
    SignValue = CheckDimMeasure(SpecValue.KindValue, Entities, ParamValue.value)
    Origin = ParamOrigin(SpanValue)
    Attributes: dict[str, object] = {
        "fusion.native_kind_code": Native.Code,
        "fusion.binding_id": Native.BindingId,
        "fusion.dimension_prefix_slot": Native.PrefixSlot,
        "fusion.annotation_position_mm": TextPosition,
    }
    if SpecValue.KindValue in (ConstraintKind.KDistanceX, ConstraintKind.KDistanceY):
        Attributes["fusion.signed_distance_multiplier"] = SignValue
        Attributes["fusion.dimension_value_convention"] = "unsigned_component"
    return SketchRelation(
        id=f"fusion-sketch-dimension-{SpanValue.ObjectId}",
        kind=SpecValue.KindValue.value,
        references=tuple(
            ConstraintRef(
                Value.id, "start" if Value.kind == GeometryKind.KPoint else ""
            )
            for Value in Entities
        ),
        parameter_id=ParamValue.id,
        driving=Driving,
        provenance=Replace(
            Origin,
            spans=Origin.spans
            + ParamOrigin(ParamSpan).spans
            + ParamOrigin(BindingSpan).spans,
        ),
        attributes=FreezeMapping(Attributes),
    )
