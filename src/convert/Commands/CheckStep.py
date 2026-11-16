from collections.abc import Mapping

from convert.Commands.GeneratorKinds import KDefinitionKinds
from interchange.document.Validation.DocumentDefValidate import GetDefErrors
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Selection import Selection
from interchange.geometry.Models.Sketch import Sketch
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.Records.RecordParameter import Parameter

# feature eligibility must exclude operations whose portable semantics are still unknown
KPortableKinds = frozenset(
    KindValue
    for KindValue in FeatureKind
    if KindValue not in (FeatureKind.KNative, FeatureKind.KImported)
)

# incomplete histories need one recovery message across generator and dependency checks
KFeatureError = (
    "IncompleteFeature records are not conversion-ready; "
    "use kit decode or kit research for inspection"
)


# feature history must provide validated definitions and supported kinds rather than descriptive labels
def CheckStep(
    Feature: FeatureStep,
    IdentitySets: Mapping[str, set[str]],
    Selections: Mapping[str, Selection],
    Parameters: Mapping[str, Parameter],
    Frames: Mapping[str, SupportPlane],
    Sketches: Mapping[str, Sketch],
) -> None:
    if Feature.kind not in KPortableKinds:
        raise ValueError(KFeatureError)
    if Feature.kind == FeatureKind.KReference:
        if Feature.definition is None and Feature.sketch_id not in Sketches:
            raise ValueError(KFeatureError)
    if (
        Feature.definition is not None
        and KDefinitionKinds.get(type(Feature.definition)) != Feature.kind
    ):
        raise ValueError(KFeatureError)
    if Feature.kind != FeatureKind.KReference and Feature.definition is None:
        raise ValueError(KFeatureError)
    if GetDefErrors(Feature, IdentitySets, Selections, Parameters, Frames, Sketches):
        raise ValueError(KFeatureError)
