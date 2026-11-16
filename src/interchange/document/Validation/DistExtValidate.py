from typing import Mapping as TypeMap

from interchange.Features.DistanceValues import GetDistValues
from interchange.Features.FeatureDistExt import DistanceExtrude
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordParameter import Parameter


# a distance extrusion must retain an actual sketch and evaluable owned parameters
def GetDistExtErrs(
    StepValue: FeatureStep,
    Definition: DistanceExtrude,
    SketchIds: set[str],
    Parameters: TypeMap[str, Parameter],
) -> tuple[str, ...]:
    Errors: list[str] = []
    if StepValue.sketch_id is None or StepValue.sketch_id not in SketchIds:
        Errors.append(f"distance extrusion {StepValue.id} requires a profile sketch")
    try:
        _ = GetDistValues(StepValue, Definition, Parameters)
    except ValueError as ErrorInfo:
        Errors.append(f"distance extrusion {StepValue.id} is invalid: {ErrorInfo}")
    return tuple(Errors)
