from collections.abc import Mapping

from convert.Commands.GeneratorKinds import KCreatorTypes
from interchange.enums.EnumFeatures import BooleanOp
from interchange.features.FeatureKinds import CombineFeature
from interchange.features.FeatureStep import FeatureStep


# geometry must depend on active typed inputs rather than unrelated feature presence
def CanGenerate(
    Feature: FeatureStep,
    Profiles: set[str],
    SketchInputs: Mapping[str, set[str]],
    Generators: set[str],
) -> bool:
    Inputs = set(Feature.input_feature_ids)
    if isinstance(Feature.definition, KCreatorTypes):
        if (
            Feature.operation != BooleanOp.KCreate
            or Feature.sketch_id not in Profiles
            or not Inputs.intersection(SketchInputs.get(Feature.sketch_id or "", set()))
        ):
            return False
        return True
    if isinstance(Feature.definition, CombineFeature):
        return (
            Feature.definition.operation
            in (BooleanOp.KJoin, BooleanOp.KCutOperation, BooleanOp.KIntersect)
            and Feature.operation in (None, Feature.definition.operation)
            and len(Inputs.intersection(Generators)) >= 2
        )
    return bool(Inputs.intersection(Generators))
