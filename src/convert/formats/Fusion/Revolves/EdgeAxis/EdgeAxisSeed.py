# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from typing import cast as CastValue

from convert.adapters.base.WriteValidate import IsObjectTuple
from convert.formats.Fusion.Extrudes.BuildExtGeom import BuildExtGeom
from convert.formats.Fusion.Extrudes.ExtrudeResult import CheckExtResult
from convert.formats.Fusion.Extrudes.SolidCreators import IsSavedActive
from convert.formats.Fusion.NativePlane import KPlaneFeature
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Sketches.SketchPlacement import KSketchFeature
from convert.formats.Fusion.Topology.ResultBody import IndexBodyLinks
from interchange.brep.topology.BrepModel import BrepModel
from interchange.enums.EnumFeatures import BooleanOp
from interchange.features.DistanceValues import GetDistValues
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Sketch import Sketch, SketchEntity
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.records.RecordParameter import Parameter


# an intervening edit must not turn initial body incidence into a later historical guess
def CheckEdgeHist(
    StepValue: FeatureStep, Creator: FeatureStep, FeatureLinks: dict[int, FeatureStep]
) -> None:
    if (
        Creator.id not in StepValue.input_feature_ids
        or Creator.order >= StepValue.order
        or not IsSavedActive(Creator)
    ):
        raise ValueError("Fusion Revolve edge creator is inactive or out of order")
    for Other in FeatureLinks.values():
        if not Creator.order < Other.order < StepValue.order:
            continue
        Origin = Other.provenance
        if (
            Origin is not None
            and Origin.spans
            and Origin.spans[0].record_kind in (KSketchFeature, KPlaneFeature)
        ):
            continue
        if IsSavedActive(Other) and Other.operation != BooleanOp.KCreate:
            raise ValueError("Fusion Revolve edge requires unmodified source topology")


# independently generated source geometry supplies neutral ids for verified native incidence
def BuildEdgeSeed(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    Creator: FeatureStep,
    NativeId: int,
    BodyId: int,
    SketchValue: Sketch,
    Frame: SupportPlane,
    Params: dict[str, Parameter],
) -> tuple[str, BrepModel, tuple[SketchEntity, ...]]:
    Definition = Creator.definition
    Attrs = Creator.attributes
    if (
        not isinstance(Definition, DistanceExtrude)
        or Definition.SideMode != "one_sided"
        or Definition.StartOffsetId is not None
        or "fusion.profile_portions" in Attrs
        or Creator.sketch_id != SketchValue.id
    ):
        raise ValueError("Fusion Revolve edge requires a straight profile prism source")
    Values = GetDistValues(Creator, Definition, Params)
    if (
        Values.LowerMm != 0.0
        or Values.UpperMm <= 0.0
        or Values.TaperRadians != 0.0
        or Values.SecondTaperRadians not in (None, 0.0)
        or Definition.Direction != Frame.transform.z_axis
    ):
        raise ValueError(
            "Fusion Revolve edge requires a positive undrafted source prism"
        )
    Identities = Attrs.get("fusion.profile_entity_ids")
    Entities = {Value.id: Value for Value in SketchValue.entities}
    if (
        not IsObjectTuple(Identities)
        or len(Identities) < 3
        or any(
            not isinstance(Identity, str) or Identity not in Entities
            for Identity in Identities
        )
        or SketchValue.closed_profile_entity_ids != (Identities,)
    ):
        raise ValueError("Fusion Revolve edge source profile membership is unresolved")
    Profile = tuple(
        Entities[Identity] for Identity in CastValue(tuple[str, ...], Identities)
    )
    if any(
        not isinstance(Value.geometry, LineGeometry) or Value.construction
        for Value in Profile
    ):
        raise ValueError(
            "Fusion Revolve edge source profile is not an ordinary line ring"
        )
    NativeBody, AnchorId = IndexBodyLinks(BulkData, Owners, frozenset({NativeId}))[
        NativeId
    ]
    if NativeBody != BodyId:
        raise ValueError("Fusion Revolve edge source body and creator result disagree")
    CheckExtResult(BulkData, Owners, NativeId, AnchorId)
    ResultId = f"fusion-derived-body-{Creator.id}"
    Model, _, _, _ = BuildExtGeom(
        ResultId, Creator, Definition, Values, SketchValue, Frame.transform
    )
    return ResultId, Model, Profile
