from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.RevolveSpan import GetAngleSpan
from interchange.records.RecordParameter import Parameter


# current parameter values remain authoritative when a body needs numeric sweep limits
def ReadAngleSpan(
    Definition: AngularRevolve, Params: dict[str, Parameter]
) -> tuple[float, float]:
    Along = Params.get(Definition.AlongParameterId)
    Against = (
        None
        if Definition.AgainstParameterId is None
        else Params.get(Definition.AgainstParameterId)
    )
    if Along is None or (Definition.AgainstParameterId is not None and Against is None):
        raise ValueError("Missing Fusion Revolve angle parameter")
    return GetAngleSpan(
        float(Along.value.value),
        None if Against is None else float(Against.value.value),
        Definition.SideMode,
    )
