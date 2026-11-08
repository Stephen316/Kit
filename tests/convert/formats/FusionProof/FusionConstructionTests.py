# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import radians as Radians

import pytest as Pytest

from convert.formats.Fusion import ReadFusionDoc
from convert.formats.Fusion.DesignZip import ReadDesignZip
from convert.formats.Fusion.NativePlane import KPlaneFeature
from convert.formats.Fusion.NumericParam import KParamGuid
from convert.formats.Fusion.ParamBinding import KBindingWidths
from convert.formats.Fusion.SourceProof.InspectSource import ReadFusionSourceProof
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.BoundPlaneValues import GetConstructionFrame
from interchange.features.FeatureBoundPlane import BoundConstructionPlane
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath
from tests.convert.formats.FusionProof.FusionNumberTests import VerifiedIds, WithBulk

# the saved capture provides independent authored controls and construction plane frames
KPlaneCases = KStudyPath / "planedefinitions-6cd0820a832e"


# qualified offset and angle controls reconstruct the same independently captured datum
@KRequiresCodec
@Pytest.mark.parametrize(
    ("Method", "ScalarValue", "Origin"),
    (("offset", 1.2, (0, 0, 12)), ("angle", Radians(35), (12.125, 0, 0))),
)
def TestConstructionRead(
    Method: str, ScalarValue: float, Origin: tuple[float, ...]
) -> None:
    Source = KPlaneCases / f"{Method}.f3d"
    Document = ReadFusionDoc(Source)
    (StepValue,) = Document.feature_timeline
    Definition = StepValue.definition
    assert isinstance(Definition, BoundConstructionPlane)
    assert Definition.Method == Method
    Params = {Value.id: Value for Value in Document.parameters}
    Scalar, Extra = (
        Params[Definition.ScalarParameterId],
        Params[Definition.OffsetParameterId],
    )
    assert Scalar.value.value == Pytest.approx(ScalarValue)
    assert Extra.value.value == 0.0
    (Plane,) = Document.support_planes
    assert Definition.SupportPlaneId == Plane.id
    Computed = GetConstructionFrame(StepValue, Definition, Params)
    assert (Computed.origin.x, Computed.origin.y, Computed.origin.z) == Pytest.approx(
        Origin
    )
    assert Computed.z_axis.y == Pytest.approx(Plane.transform.z_axis.y)
    assert Computed.z_axis.z == Pytest.approx(Plane.transform.z_axis.z)
    assert CadDocument.from_json(Document.to_json()) == Document
    Coverage = ReadFusionSourceProof(Source)
    assert len(VerifiedIds(Coverage, frozenset({KParamGuid}))) == 2
    assert len(VerifiedIds(Coverage, frozenset(KBindingWidths))) == 2
    assert not Coverage.IsComplete


# changing only the authored method cannot turn a surviving cached frame into a typed plane
@KRequiresCodec
def TestConstructionRouteGuard() -> None:
    Source = KPlaneCases / "angle.f3d"
    Original = ReadFusionDoc(Source)
    BulkData, Spans = ReadDesignZip(Source.read_bytes())
    (PlaneFeature,) = tuple(
        Span for Span in Spans if Span.IsPrimary and Span.ClassGuid == KPlaneFeature
    )
    Edited = bytearray(BulkData)
    Edited[PlaneFeature.PayloadOffset + 4 + 3] ^= 1
    Mutated = WithBulk(Source, bytes(Edited))
    Readback = ReadFusionDoc(Mutated)
    assert Readback.support_planes[0].transform == Original.support_planes[0].transform
    assert Readback.feature_timeline[0].definition is None
    assert not VerifiedIds(ReadFusionSourceProof(Mutated), frozenset(KBindingWidths))
