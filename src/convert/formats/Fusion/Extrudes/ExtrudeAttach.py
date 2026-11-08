# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as Replace
from math import isclose as IsClose

from convert.formats.Fusion.Extrudes.ExtrudeRead import ReadExtrude
from convert.formats.Fusion.Extrudes.ExtParamLinks import BindExtParams
from convert.formats.Fusion.ParamProjection import ParamOrigin
from convert.formats.Fusion.RecordSpan import RecordSpan
from interchange.enums.EnumFeatures import BooleanOp
from interchange.features.DistanceValues import GetDistValues
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.geometry.models.VectorSpace import SpaceVector
from interchange.records.RecordParameter import Parameter


# editable extrusions retain the verified profile and component direction with live parameter links
def AttachDistExt(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    StepValue: FeatureStep,
    FrameValue: SupportPlane | None,
    Params: dict[str, Parameter],
) -> FeatureStep:
    Origin = StepValue.provenance
    ProfileId = StepValue.attributes.get("fusion.profile_descriptor_id")
    if Origin is None or FrameValue is None or type(ProfileId) is not int:
        raise ValueError("Missing verified Fusion Extrude profile and frame")
    FeatureId = int(Origin.native_id)
    Native = ReadExtrude(BulkData, Owners, FeatureId)
    if Native.ProfileId != ProfileId:
        raise ValueError("Fusion Extrude profile proxy and projected profile disagree")
    Normal = FrameValue.transform.z_axis
    if any(
        not IsClose(Actual, Expected, abs_tol=1e-9, rel_tol=0.0)
        for Actual, Expected in zip(Native.Direction, (Normal.x, Normal.y, Normal.z))
    ):
        raise ValueError(
            "Fusion Extrude direction is outside its verified component frame"
        )
    Links = BindExtParams(StepValue, FeatureId, Native, Params)
    Definition = DistanceExtrude(
        AlongParameterId=Links[Native.AlongId],
        Direction=SpaceVector(*Native.Direction),
        SideMode=Native.SideMode,
        AgainstParameterId=(
            Links.get(Native.AgainstId) if Native.AgainstId is not None else None
        ),
        StartOffsetId=Links.get(Native.StartId) if Native.StartId is not None else None,
        TaperParameterId=(
            Links.get(Native.TaperId) if Native.TaperId is not None else None
        ),
        SecondTaperId=(
            Links.get(Native.SecondTaperId)
            if Native.SecondTaperId is not None
            else None
        ),
    )
    Updated = Replace(
        StepValue,
        operation=BooleanOp.KCreate,
        definition=Definition,
        provenance=Replace(
            Origin, spans=Origin.spans + ParamOrigin(Owners[Native.ProxyId]).spans
        ),
    )
    GetDistValues(Updated, Definition, Params)
    return Updated
