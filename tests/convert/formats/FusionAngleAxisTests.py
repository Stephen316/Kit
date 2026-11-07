# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import replace as Replace
from struct import pack as Pack

from pytest import raises as Raises

from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Revolves.AngularAxis import ResolveAngleAxis
from convert.formats.Fusion.SelectionRef import KSelectLeaf
from convert.formats.Fusion.Topology.PickSupport import KSupportGuid
from interchange.core.Common import FreezeMapping
from interchange.enums.EnumFeatures import FeatureKind
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector
from interchange.records.RecordProvenance import Provenance
from tests.convert.formats.FusionHistoryTests import NativeRef
from tests.convert.formats.FusionOriginAxisTests import AxisFixture
from tests.convert.formats.FusionRevolveTests import SelectFixture


# a typed origin axis still needs an exact reciprocal revolved selection
def TestAngleAxisPick() -> None:
    BodyData, Owners = AxisFixture(40)
    PickData, PickOwners = SelectFixture(KSelectLeaf, bytes(2) + Pack("<Q", 40))
    SupportPos = PickOwners[21].PayloadOffset + 4 + 240
    PickData[SupportPos : SupportPos + 11] = NativeRef(23)
    Offset = len(BodyData)
    Owners.update(
        (
            Identity,
            Replace(
                SpanValue,
                StartOffset=SpanValue.StartOffset + Offset,
                PayloadOffset=SpanValue.PayloadOffset + Offset,
                EndOffset=SpanValue.EndOffset + Offset,
            ),
        )
        for Identity, SpanValue in PickOwners.items()
    )
    BulkData = bytearray(BodyData) + PickData
    Start = len(BulkData)
    BulkData.extend(
        bytes(4)
        + bytes(6)
        + b"\1\1"
        + Pack("<I", 1)
        + NativeRef(21)
        + bytes(8)
        + NativeRef(21)
        + bytes(16)
    )
    Owners[23] = RecordSpan(
        Start, Start, len(BulkData), 23, 256, KSupportGuid, "", True
    )
    StepValue = FeatureStep(
        id="revolve",
        name="Angular Revolve",
        kind=FeatureKind.KRevolution,
        order=1,
        provenance=Provenance(adapter="fusion.f3d", native_id="10"),
        attributes=FreezeMapping(
            {
                "fusion.revolve.axis_selection_id": 20,
                "fusion.revolve.axis_object_id": 40,
            }
        ),
    )
    Frame = SupportPlane(
        id="frame",
        name="Profile frame",
        transform=Transform(),
        attributes=FreezeMapping({"fusion.component_object_id": 3}),
    )
    PickValue, Origin, Direction = ResolveAngleAxis(
        bytes(BulkData), Owners, StepValue, (), {}, {}, Frame
    )
    assert PickValue.query == {"kind": "component_origin_axis", "axis": "Y"}
    assert PickValue.provenance is not None and len(PickValue.provenance.spans) == 6
    assert Origin == SpaceVector(0.0, 0.0, 0.0)
    assert Direction == SpaceVector(0.0, 1.0, 0.0)
    BulkData[Start + 35 : Start + 46] = NativeRef(22)
    with Raises(ValueError, match="support owner disagrees"):
        ResolveAngleAxis(bytes(BulkData), Owners, StepValue, (), {}, {}, Frame)
