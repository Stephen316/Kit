# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as Replace

import pytest as Pytest

from convert.formats.Fusion.NumericParam import ReadNativeNum
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SourceProof.Bindings.ReadBindingProof import (
    ReadBindingProof,
)
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureBoundPlane import BoundConstructionPlane
from interchange.geometry.models.VectorSpace import SpaceVector
from interchange.records.RecordParameter import Parameter
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec
from tests.convert.formats.FusionProof.FusionBindingProofTests import (
    BindFixture,
    BoundParams,
)


# native plane records must substantiate the exact parameters present in the neutral definition
def PlaneBind(
    Bulk: bytes,
    Owners: dict[int, RecordSpan],
    Document: CadDocument,
    ParamValue: Parameter,
    RankValue: int,
) -> RecordSpan:
    Origin = ParamValue.provenance
    assert Origin is not None
    Span = Owners[int(Origin.native_id)]
    Native = ReadNativeNum(Bulk[Span.PayloadOffset + 4 : Span.EndOffset])
    return ReadBindingProof(Bulk, Owners, Document, Native, Span, ParamValue, RankValue)


# signed angle and positive offset methods bind independently of the consuming feature
@KRequiresCodec
@Pytest.mark.parametrize(
    ("Sample", "Method", "Count"),
    (
        ("extents-f0f33a9a605f/from_plane.f3d", "offset", 2),
        ("extents-f0f33a9a605f/to_plane_offset.f3d", "offset", 2),
        ("revolveto-b1d196f65c46/negative_plane.f3d", "angle", 2),
        ("revolveto-b1d196f65c46/two_planes.f3d", "angle", 4),
    ),
)
def TestPlaneBind(Sample: str, Method: str, Count: int) -> None:
    Bulk, Owners, Document = BindFixture(Sample)
    PlaneSteps = {
        Value.id: Value.definition.Method
        for Value in Document.feature_timeline
        if isinstance(Value.definition, BoundConstructionPlane)
    }
    Actual = 0
    for RankValue, ParamValue in enumerate(BoundParams(Document), 1):
        if ParamValue.owner_id not in PlaneSteps:
            continue
        assert PlaneSteps[ParamValue.owner_id] == Method
        Binding = PlaneBind(Bulk, Owners, Document, ParamValue, RankValue)
        assert Binding.ObjectId == ParamValue.attributes["fusion.binding_id"]
        Actual += 1
    assert Actual == Count


# each projection input must remain tied to the independently authored native plane
@KRequiresCodec
def TestPlaneBindGuard() -> None:
    Bulk, Owners, Document = BindFixture("revolveto-b1d196f65c46/negative_plane.f3d")
    Scalar, Offset, _ = BoundParams(Document)
    StepValue = next(
        Value for Value in Document.feature_timeline if Value.id == Scalar.owner_id
    )
    Definition = StepValue.definition
    assert (
        isinstance(Definition, BoundConstructionPlane)
        and StepValue.provenance is not None
    )
    FrameValue = next(
        Value
        for Value in Document.support_planes
        if Value.id == Definition.SupportPlaneId
    )
    Edited = Replace(
        FrameValue, transform=Replace(FrameValue.transform, origin=SpaceVector(7, 0, 0))
    )
    Changed = Replace(
        Document,
        support_planes=tuple(
            Edited if Value.id == FrameValue.id else Value
            for Value in Document.support_planes
        ),
    )
    with Pytest.raises(ValueError, match="construction datum disagrees"):
        PlaneBind(Bulk, Owners, Changed, Scalar, 1)
    NewDef = Replace(
        Definition,
        ReferenceFrame=Replace(Definition.ReferenceFrame, origin=SpaceVector(0, 1, 0)),
    )
    Changed = Replace(
        Document,
        feature_timeline=tuple(
            Replace(Value, definition=NewDef) if Value.id == StepValue.id else Value
            for Value in Document.feature_timeline
        ),
    )
    with Pytest.raises(ValueError, match="authoring frame disagrees"):
        PlaneBind(Bulk, Owners, Changed, Scalar, 1)
    NewOffset = Replace(Offset, value=Replace(Offset.value, value=2.0))
    Changed = Replace(
        Document,
        parameters=tuple(
            NewOffset if Value.id == Offset.id else Value
            for Value in Document.parameters
        ),
    )
    with Pytest.raises(ValueError, match="construction parameter disagrees"):
        PlaneBind(Bulk, Owners, Changed, Scalar, 1)
    Owner = Owners[int(StepValue.provenance.native_id)]
    BackendStart = Owner.PayloadOffset + 4 + 31
    Backend = Owners[int.from_bytes(Bulk[BackendStart : BackendStart + 8], "little")]
    EditedBulk = bytearray(Bulk)
    EditedBulk[Backend.EndOffset - 10] ^= 1
    with Pytest.raises(ValueError, match="backend owner"):
        PlaneBind(bytes(EditedBulk), Owners, Document, Scalar, 1)
