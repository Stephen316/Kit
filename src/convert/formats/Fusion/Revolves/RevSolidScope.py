from convert.formats.Fusion.NativePlane import KPlaneFeature
from convert.formats.Fusion.Sketches.SketchPlacement import KSketchFeature
from interchange.enums.EnumFeatures import FeatureKind
from interchange.features.FeatureStep import FeatureStep


# active new body operations can be reconstructed independently without guessing boolean history
def FindRevCreators(Steps: tuple[FeatureStep, ...]) -> tuple[FeatureStep, ...]:
    Creators: list[FeatureStep] = []
    ByIdentity = {StepValue.id: StepValue for StepValue in Steps}
    for StepValue in Steps:
        Origin = StepValue.provenance
        if (
            Origin is not None
            and Origin.spans
            and Origin.spans[0].record_kind in (KSketchFeature, KPlaneFeature)
        ):
            continue
        Attrs = StepValue.attributes
        if (
            StepValue.kind != FeatureKind.KRevolution
            or Attrs.get("fusion.revolve.operation") != "new_body"
            or Attrs.get("fusion.revolve.solid") is not True
            or Attrs.get("fusion.revolve.project_axis") is not False
        ):
            raise ValueError(
                "Fusion history includes modeling outside independent solid Revolves"
            )
        Creators.append(StepValue)
    RelevantIds = {
        Identity
        for Creator in Creators
        for Identity in (Creator.id, *Creator.input_feature_ids)
    }
    if any(
        (Source := ByIdentity.get(Identity)) is None
        or Source.suppressed
        or Source.attributes.get("fusion.state_known") is not True
        or Source.attributes.get("fusion.rolled_back") is not False
        for Identity in RelevantIds
    ):
        raise ValueError("Fusion Revolve or a required input is inactive or unverified")
    return tuple(Creators)
