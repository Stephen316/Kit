# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from re import fullmatch as FullMatch

from convert.formats.Fusion.NativeParam import NativeParam
from convert.formats.Fusion.NumericParam import KParamGuid, ReadNativeNum
from convert.formats.Fusion.ParamBinding import ResolveOwner
from convert.formats.Fusion.ParamProjection import ParamQuantity
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Sketches.Dimensional.DimRecord import DimRecordBody
from convert.formats.Fusion.Sketches.Dimensional.DimSpec import DimensionSpec
from convert.formats.Fusion.Sketches.SketchPlacement import KSketchFeature
from interchange.records.RecordParameter import Parameter

# sketch dimensions use the proved floating point numeric binding representation
KDimBindingGuid = "D91D429C-1BB5-4640-B49F-69AF14F463E9"


# reciprocal primary ownership rejects coincident values belonging to other parameters
def ReadDimParam(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    ParamValue: Parameter,
    BindingId: int,
    FeatureId: int,
    SpecValue: DimensionSpec,
) -> tuple[NativeParam, RecordSpan, RecordSpan]:
    Origin = ParamValue.provenance
    if (
        Origin is None
        or Origin.adapter != "fusion.f3d"
        or not Origin.native_id.isascii()
        or not Origin.native_id.isdecimal()
    ):
        raise ValueError("Missing native Fusion dimension parameter identity")
    ParamSpan = Owners.get(int(Origin.native_id))
    if (
        ParamSpan is None
        or ParamSpan.ClassGuid != KParamGuid
        or ParamValue.id != f"fusion-parameter-{ParamSpan.ObjectId}"
        or ParamValue.attributes.get("fusion.owner_object_id") != FeatureId
        or ParamValue.attributes.get("fusion.owner_class_guid") != KSketchFeature
        or FullMatch(rf"fusion-feature-[0-9]+-{FeatureId}", ParamValue.owner_id) is None
    ):
        raise ValueError(
            "Fusion dimension parameter does not belong to its sketch feature"
        )
    Native = ReadNativeNum(DimRecordBody(BulkData, ParamSpan))
    if (
        Native.BindingId != BindingId
        or ParamValue.attributes.get("fusion.binding_id") != BindingId
        or Native.ParamName != ParamValue.name
        or Native.RoleName != ParamValue.attributes.get("fusion.native_role")
        or FullMatch(rf"{SpecValue.RolePrefix} Dimension-[1-9][0-9]*", Native.RoleName)
        is None
        or ParamValue.value != ParamQuantity(Native)
        or ParamValue.expression is None
        or ParamValue.expression.source != Native.Formula
        or ParamValue.expression.language != "fusion"
    ):
        raise ValueError("Fusion dimensional parameter role or value disagrees")
    Resolved = ResolveOwner(BulkData, Owners, Native, ParamSpan)
    if (
        Resolved is None
        or Resolved[0].ObjectId != FeatureId
        or Resolved[1].ClassGuid != KDimBindingGuid
    ):
        raise ValueError("Fusion dimensional numeric binding is unsupported")
    return Native, ParamSpan, Resolved[1]
