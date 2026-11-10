# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.formats.Fusion.NativePlane import KPlaneFeature
from convert.formats.Fusion.Sketches.SketchPlacement import KSketchFeature
from interchange.enums.EnumFeatures import BooleanOp
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeaturePlaneExt import PlaneExtrude
from interchange.features.FeaturePlaneRev import PlaneRevolve
from interchange.features.FeatureStep import FeatureStep


# saved rollback and suppression determine whether a creator can contribute a body
def IsSavedActive(StepValue: FeatureStep) -> bool:
    if StepValue.attributes.get("fusion.state_known") is not True:
        raise ValueError("Fusion modeling or source feature has unverified saved state")
    return (
        not StepValue.suppressed
        and StepValue.attributes.get("fusion.rolled_back") is False
    )


# final geometry requires that all active modeling steps create independent solids
def FindExtCreators(Steps: tuple[FeatureStep, ...]) -> tuple[FeatureStep, ...]:
    ByStep = {StepValue.id: StepValue for StepValue in Steps}
    Creators: list[FeatureStep] = []
    for StepValue in Steps:
        Origin = StepValue.provenance
        if (
            Origin is not None
            and Origin.spans
            and Origin.spans[0].record_kind in (KSketchFeature, KPlaneFeature)
        ):
            continue
        if not IsSavedActive(StepValue):
            continue
        if StepValue.operation != BooleanOp.KCreate or not isinstance(
            StepValue.definition,
            (DistanceExtrude, PlaneExtrude, AngularRevolve, PlaneRevolve),
        ):
            raise ValueError(
                "Fusion history contains active modeling outside independent solid Extrudes and Revolves"
            )
        for Identity in StepValue.input_feature_ids:
            Source = ByStep.get(Identity)
            if Source is None or not IsSavedActive(Source):
                raise ValueError(
                    "Fusion solid creator has an inactive or missing source feature"
                )
        Creators.append(StepValue)
    return tuple(Creators)
