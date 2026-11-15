from typing import Mapping

from convert.adapters.solidworks.core.Native import NativeEquation
from interchange import frozen_mapping as FrozenMapping

# target resolution failures need a durable interchange key for write policy
KUnresolvedEqTargets = "solidworks.unresolvedEquationReferences"


# equation targets must identify an authored dimension before the expression can drive it
def ResolveTarget(
    Equation: NativeEquation,
    DimensionIds: Mapping[tuple[str, str], str],
    AmbiguousKeys: frozenset[tuple[str, str]],
    ParamIndexes: Mapping[str, int],
) -> tuple[int | None, Mapping[str, object] | None]:
    DimensionName, FeatureName = Equation.lhs.split("@", 1)
    QualifiedName = (FeatureName, DimensionName)
    ParamId = DimensionIds.get(QualifiedName)
    IsAmbiguous = QualifiedName in AmbiguousKeys
    if not IsAmbiguous and ParamId is not None and ParamId in ParamIndexes:
        return ParamIndexes[ParamId], None
    return None, FrozenMapping(
        {
            "lhs": Equation.lhs,
            "equation_source": Equation.source,
            "equation_configuration_id": Equation.configuration_id,
            "native_stream": Equation.native_stream,
            "native_offset": Equation.native_offset,
            "native_length": Equation.native_length,
            "reason": "ambiguous_target" if IsAmbiguous else "unresolved_target",
        }
    )
