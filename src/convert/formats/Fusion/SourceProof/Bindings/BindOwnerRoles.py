# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.formats.Fusion.BodyInputs.ScaleControls import ReadScaleData
from convert.formats.Fusion.NativePlane import KPlaneFeature
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SourceProof.Bindings.BindExtRoles import (
    DistBindRoles,
    PlaneBindRoles,
)
from convert.formats.Fusion.SourceProof.Bindings.BindPlaneRoles import DatumBindRoles
from convert.formats.Fusion.SourceProof.Bindings.BindingRoles import KBindingRoles
from convert.formats.Fusion.SourceProof.Bindings.BindRevRoles import RevBindRoles
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.FeatureBoundScale import BoundScale
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeaturePlaneExt import PlaneExtrude
from interchange.features.FeaturePlaneRev import PlaneRevolve
from interchange.features.FeatureStep import FeatureStep
from interchange.records.RecordParameter import Parameter


# uniform scale also carries a second independent numeric cache in its feature header
def ScaleBindRoles(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    OwnerId: int,
    Definition: BoundScale,
    ParamValue: Parameter,
) -> KBindingRoles:
    Native = ReadScaleData(BulkData, Owners, OwnerId)
    Identities = Definition.FactorParameterIds
    if len(Identities) != len(Native.FactorIds):
        raise ValueError("Fusion Scale factor binding count disagrees")
    if len(Identities) == 1 and Native.CachedFactor != ParamValue.value.value:
        raise ValueError("Fusion Scale uniform factor and feature cache disagree")
    Roles = ("ScaleFactor",) if len(Identities) == 1 else ("ScaleX", "ScaleY", "ScaleZ")
    return tuple(
        (NativeId, ParamId, RoleName, "")
        for NativeId, ParamId, RoleName in zip(
            Native.FactorIds, Identities, Roles, strict=True
        )
    )


# independent native feature controls establish the role of each binding
def BindOwnerRoles(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    Document: CadDocument,
    OwnerValue: RecordSpan,
    StepValue: FeatureStep,
    ParamValue: Parameter,
) -> KBindingRoles:
    if BulkData[OwnerValue.PayloadOffset : OwnerValue.PayloadOffset + 4] != bytes(4):
        raise ValueError("Unsupported Fusion binding owner payload prefix")
    if OwnerValue.ClassGuid == KPlaneFeature:
        return DatumBindRoles(BulkData, Owners, Document, OwnerValue, StepValue)
    Definition = StepValue.definition
    OwnerId = OwnerValue.ObjectId
    if isinstance(Definition, DistanceExtrude):
        return DistBindRoles(BulkData, Owners, OwnerId, Definition)
    if isinstance(Definition, PlaneExtrude):
        return PlaneBindRoles(BulkData, Owners, OwnerId, Definition)
    if isinstance(Definition, (AngularRevolve, PlaneRevolve)):
        return RevBindRoles(BulkData, OwnerValue, StepValue, Definition)
    if isinstance(Definition, BoundScale):
        return ScaleBindRoles(BulkData, Owners, OwnerId, Definition, ParamValue)
    raise ValueError("Unsupported Fusion binding owner control route")
