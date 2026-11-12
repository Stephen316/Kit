from convert.formats.Fusion.BodyInputs.ScaleControls import ScaleControls
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.BoundScaleValues import ReadScaleFactor
from interchange.features.FeatureStep import FeatureStep


# each axis uses the exact reciprocal native parameter binding and role
def ReadScaleParams(
    Document: CadDocument, StepValue: FeatureStep, FeatureId: int, Fields: ScaleControls
) -> tuple[str, ...]:
    Roles = (
        ("ScaleFactor",)
        if len(Fields.FactorIds) == 1
        else ("ScaleX", "ScaleY", "ScaleZ")
    )
    Params = {Value.id: Value for Value in Document.parameters}
    Identities: list[str] = []
    for BindingId, RoleValue in zip(Fields.FactorIds, Roles, strict=True):
        Matches = tuple(
            Value.id
            for Value in Params.values()
            if Value.attributes.get("fusion.binding_id") == BindingId
            and Value.attributes.get("fusion.owner_object_id") == FeatureId
            and Value.attributes.get("fusion.native_role") == RoleValue
        )
        if len(Matches) != 1:
            raise ValueError("Fusion Scale factor binding or axis role disagrees")
        (Identity,) = Matches
        Factor = ReadScaleFactor(StepValue, Identity, Params)
        if len(Roles) == 1 and Factor != Fields.CachedFactor:
            raise ValueError("Fusion Scale uniform factor and feature cache disagree")
        Identities.append(Identity)
    return tuple(Identities)
