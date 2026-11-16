from interchange.brep.Validation.BrepBodyValidate import GetBodyErrors
from interchange.brep.Validation.BrepCurveValidate import GetCurveErrors
from interchange.brep.Validation.BrepEdgeValidate import GetEdgeErrors
from interchange.brep.Validation.BrepFaceValidate import GetFaceErrors
from interchange.brep.Validation.BrepIdentityValidate import GetBrepIds
from interchange.brep.Validation.BrepLoopValidate import GetLoopErrors
from interchange.brep.Validation.BrepPcurveValidate import GetPcurveErrors
from interchange.brep.Validation.BrepShellValidate import GetShellErrors
from interchange.brep.Validation.BrepSurfaceValidate import GetSurfErrors
from interchange.brep.Validation.BrepView import BrepView


# validation orchestration preserves deterministic diagnostics across focused topology checks
def GetBrepErrors(
    ModelValue: BrepView, DesignBodyIds: frozenset[str]
) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    if (
        not ModelValue.schema_version.strip()
        or ModelValue.schema_version != ModelValue.schema_version.strip()
    ):
        ErrorValues.append("B-rep schema version must be a non-empty string")
    IdentitySets, IdentityErrors = GetBrepIds(ModelValue)
    ErrorValues.extend(IdentityErrors)
    for CurveValue in ModelValue.curves:
        ErrorValues.extend(GetCurveErrors(CurveValue, IdentitySets["Surfaces"]))
    for PcurveValue in ModelValue.pcurves:
        ErrorValues.extend(GetPcurveErrors(PcurveValue))
    for SurfaceValue in ModelValue.surfaces:
        ErrorValues.extend(GetSurfErrors(SurfaceValue, IdentitySets["Surfaces"]))
    ErrorValues.extend(GetEdgeErrors(ModelValue, IdentitySets))
    ErrorValues.extend(GetLoopErrors(ModelValue, IdentitySets))
    ErrorValues.extend(GetFaceErrors(ModelValue, IdentitySets))
    ErrorValues.extend(GetShellErrors(ModelValue, IdentitySets))
    ErrorValues.extend(GetBodyErrors(ModelValue, IdentitySets, DesignBodyIds))
    return tuple(ErrorValues)
