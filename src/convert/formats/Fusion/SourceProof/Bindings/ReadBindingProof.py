# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.NativeParam import NativeParam
from convert.formats.Fusion.NumericParam import KParamGuid
from convert.formats.Fusion.ParamProjection import ParamOrigin, ParamQuantity
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SourceProof.Bindings.BindOwnerRoles import BindOwnerRoles
from convert.formats.Fusion.SourceProof.Bindings.BindRecord import ReadBindRecord
from convert.formats.Fusion.SourceProof.Bindings.BindingRoles import KBindingRoles
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureStep import FeatureStep
from interchange.records.RecordParameter import Parameter


# native identities prevent one projected timeline entry from impersonating another owner
def FindBindOwner(
    Document: CadDocument, OwnerValue: RecordSpan, ParamValue: Parameter
) -> FeatureStep:
    NativeId = str(OwnerValue.ObjectId)
    Candidates = tuple(
        Value
        for Value in Document.feature_timeline
        if Value.id == ParamValue.owner_id
        or (Value.provenance is not None and Value.provenance.native_id == NativeId)
    )
    if len(Candidates) != 1:
        raise ValueError("Missing or ambiguous projected Fusion binding owner")
    (StepValue,) = Candidates
    Origin = StepValue.provenance
    if (
        StepValue.id != ParamValue.owner_id
        or ParamValue.id not in StepValue.parameter_ids
        or Origin is None
        or Origin.adapter != "fusion.f3d"
        or Origin.native_id != NativeId
        or ParamOrigin(OwnerValue).spans[0] not in Origin.spans
    ):
        raise ValueError("Projected Fusion binding owner disagrees")
    return StepValue


# optional feature controls are omitted from slot order only when absent in both representations
def CheckBindRole(
    Roles: KBindingRoles,
    SlotValue: int,
    BindingId: int,
    RoleName: str,
    ParamValue: Parameter,
) -> None:
    if any(
        (NativeId is None) != (ParamId is None) for NativeId, ParamId, _, _ in Roles
    ):
        raise ValueError("Fusion binding projected role list disagrees")
    Active = tuple(Value for Value in Roles if Value[0] is not None)
    if (
        len({Value[0] for Value in Active}) != len(Active)
        or len({Value[1] for Value in Active}) != len(Active)
        or SlotValue >= len(Active)
        or Active[SlotValue]
        != (BindingId, ParamValue.id, RoleName, ParamValue.value.unit)
    ):
        raise ValueError("Fusion numeric binding owner control slot disagrees")


# only complete reciprocal bindings can be promoted independently of their auxiliary support
def ReadBindingProof(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    Document: CadDocument,
    ParamData: NativeParam,
    ParamSpan: RecordSpan,
    ParamValue: Parameter,
    BoundRank: int,
) -> RecordSpan:
    Attrs = ParamValue.attributes
    if (
        not ParamSpan.IsPrimary
        or ParamSpan.ClassGuid != KParamGuid
        or Owners.get(ParamSpan.ObjectId) != ParamSpan
        or ParamValue.id != f"fusion-parameter-{ParamSpan.ObjectId}"
        or ParamValue.value != ParamQuantity(ParamData)
        or type(BoundRank) is not int
        or BoundRank <= 0
        or Attrs.get("fusion.native_role") != ParamData.RoleName
        or Attrs.get("fusion.binding_id") != ParamData.BindingId
    ):
        raise ValueError("Fusion numeric binding proof parameter identity disagrees")
    OwnerValue, Binding, SlotValue = ReadBindRecord(
        BulkData, Owners, ParamData, ParamSpan, BoundRank
    )
    Origin = ParamValue.provenance
    if (
        Attrs.get("fusion.owner_object_id") != OwnerValue.ObjectId
        or Attrs.get("fusion.owner_class_guid") != OwnerValue.ClassGuid
        or Origin is None
        or Origin.adapter != "fusion.f3d"
        or Origin.native_id != str(ParamSpan.ObjectId)
        or Origin.spans != ParamOrigin(ParamSpan).spans + ParamOrigin(Binding).spans
    ):
        raise ValueError("Projected Fusion numeric binding provenance disagrees")
    StepValue = FindBindOwner(Document, OwnerValue, ParamValue)
    Roles = BindOwnerRoles(
        BulkData, Owners, Document, OwnerValue, StepValue, ParamValue
    )
    CheckBindRole(Roles, SlotValue, Binding.ObjectId, ParamData.RoleName, ParamValue)
    return Binding
