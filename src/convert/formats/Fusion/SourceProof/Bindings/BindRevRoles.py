# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.formats.Fusion.FeatureLabels import KFeatureFields
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Revolves.RevolveRead import ReadRevInputs
from convert.formats.Fusion.SourceProof.Bindings.BindingRoles import KBindingRoles
from interchange.enums.EnumFeatures import FeatureKind
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.FeaturePlaneRev import PlaneRevolve
from interchange.features.FeatureStep import FeatureStep


# inactive along angles on entity limits retain a distinct proven control route
def RevBindRoles(
    BulkData: bytes,
    OwnerValue: RecordSpan,
    StepValue: FeatureStep,
    Definition: AngularRevolve | PlaneRevolve,
) -> KBindingRoles:
    Fields = KFeatureFields.get(OwnerValue.ClassGuid)
    if Fields is None or Fields[1] != FeatureKind.KRevolution:
        raise ValueError("Fusion angle binding does not own a typed Revolve")
    Native = ReadRevInputs(
        BulkData[OwnerValue.PayloadOffset + 4 : OwnerValue.EndOffset]
    )
    if Native.Operation != "new_body" or not Native.IsSolid or Native.IsProjected:
        raise ValueError("Unsupported Fusion binding Revolve operation")
    if isinstance(Definition, AngularRevolve):
        if Native.ExtentKind != "angle" or Native.SideMode != Definition.SideMode:
            raise ValueError("Fusion Revolve angle binding owner mode disagrees")
        return (
            (Native.AlongId, Definition.AlongParameterId, "AlongAngle", "rad"),
            (Native.AgainstId, Definition.AgainstParameterId, "AgainstAngle", "rad"),
        )
    AlongId = StepValue.attributes.get("fusion.revolve.along_parameter_id")
    if (
        Native.ExtentKind != "to_entity"
        or len(Native.TargetIds) != len(Definition.PlaneSelectionIds)
        or StepValue.attributes.get("fusion.revolve.along_active") is not False
        or not isinstance(AlongId, str)
    ):
        raise ValueError("Fusion plane Revolve inactive binding disagrees")
    return ((Native.AlongId, AlongId, "AlongAngle", "rad"),)
