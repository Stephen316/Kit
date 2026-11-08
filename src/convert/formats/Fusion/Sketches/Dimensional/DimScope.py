# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Sketches.Dimensional.DimRecord import DimRecordBody
from convert.formats.Fusion.Sketches.SketchPlacement import KSketchFeature
from convert.formats.Fusion.Sketches.SketchRuleScope import IndexRuleEnts
from interchange.geometry.models.Sketch import Sketch, SketchEntity
from interchange.records.RecordParameter import Parameter


# one sketch scope indexes only the parameters and entities owned by its feature
@MakeDataClass(frozen=True, slots=True)
class DimensionScope:
    FeatureId: int
    Bindings: dict[int, tuple[Parameter, ...]]
    Entities: dict[int, SketchEntity]


# the native parameter owner must be the reciprocal feature of this sketch root
def ReadDimFeature(
    BulkData: bytes, Owners: dict[int, RecordSpan], RootSpan: RecordSpan
) -> int:
    RootData = DimRecordBody(BulkData, RootSpan)
    if len(RootData) < 15:
        raise ValueError("Truncated Fusion dimension sketch root")
    FeatureId = ReadNativeRef(MetaCursor(RootData[-15:]))
    Feature = Owners.get(FeatureId)
    if Feature is None or Feature.ClassGuid != KSketchFeature:
        raise ValueError("Fusion dimension sketch feature is unresolved")
    Cursor = MetaCursor(DimRecordBody(BulkData, Feature))
    Cursor.Offset = 3
    Count = Cursor.ReadCount(1024)
    Cursor.Offset = 12 + 11 * Count
    if ReadNativeRef(Cursor) != RootSpan.ObjectId:
        raise ValueError("Fusion dimension sketch feature ownership disagrees")
    return FeatureId


# no same valued or same named unbound parameter may replace the native binding
def IndexDimBinds(
    SketchValue: Sketch, Parameters: dict[str, Parameter]
) -> dict[int, tuple[Parameter, ...]]:
    Result: dict[int, list[Parameter]] = {}
    if len(set(SketchValue.parameter_ids)) != len(SketchValue.parameter_ids):
        raise ValueError("Ambiguous Fusion dimension sketch parameter membership")
    for ParamId in SketchValue.parameter_ids:
        ParamValue = Parameters.get(ParamId)
        if ParamValue is None:
            continue
        BindingId = ParamValue.attributes.get("fusion.binding_id")
        if type(BindingId) is int and BindingId > 0:
            Result.setdefault(BindingId, []).append(ParamValue)
    return {Identity: tuple(Values) for Identity, Values in Result.items()}


# native root membership is independently corroborated by both feature and operand records
def ReadDimScope(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    Parameters: dict[str, Parameter],
    RootSpan: RecordSpan,
    SketchValue: Sketch,
) -> DimensionScope:
    return DimensionScope(
        ReadDimFeature(BulkData, Owners, RootSpan),
        IndexDimBinds(SketchValue, Parameters),
        IndexRuleEnts(BulkData, Owners, SketchValue, RootSpan.ObjectId),
    )
