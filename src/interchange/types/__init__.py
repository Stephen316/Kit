from interchange.Core.Common import FreezeMapping, KJsonScalar, KJsonValue
from interchange.Enums.EnumDocument import Capability, Severity
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Enums.EnumGeometry import ConstraintKind, GeometryKind
from interchange.Enums.EnumUnits import UnitSystem
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Records.RecordConfig import Configuration, ParamOverride
from interchange.Records.RecordDiagnostic import Diagnostic
from interchange.Records.RecordParameter import Expression, Parameter, ParameterValue
from interchange.Records.RecordProvenance import Provenance, ProvenanceSpan
from interchange.Records.RecordSource import CadSource
from interchange.Records.RecordTopology import TopologyCounts
from interchange.Compatibility.PythonCompat import BindCompatMut
from interchange.Compatibility.PublicMetadata import (
    BindFunctionMut,
    BindModules,
    BindNameMut,
)
from interchange.geometry.Models.Vectors import (
    BoundingBox,
    PlaneVector,
    SpaceVector,
    Transform,
)
from inspect import Parameter as FuncParam
from inspect import Signature as FuncSig

BindNameMut(BooleanOp, __name__, "BooleanOperation", globals())
BindModules(
    (
        Capability,
        ConstraintKind,
        FeatureKind,
        GeometryKind,
        ParameterRole,
        Severity,
        UnitSystem,
        ValueKind,
    ),
    __name__,
)

BindCompatMut(
    (
        PlaneVector,
        SpaceVector,
        Transform,
        BoundingBox,
        ProvenanceSpan,
        Provenance,
        ParameterValue,
        Expression,
        Parameter,
        ParamOverride,
        Configuration,
        CadSource,
        Diagnostic,
    ),
    {__name__: globals()},
)

# the public json scalar name must remain available so existing integrations keep resolving the canonical implementation
JsonScalar = KJsonScalar

# the public json value name must remain available so existing integrations keep resolving the canonical implementation
JsonValue = KJsonValue

# the public boolean operation name must remain available so existing integrations keep resolving the canonical implementation
BooleanOperation = BooleanOp

# the public parameter override name must remain available so existing integrations keep resolving the canonical implementation
ParameterOverride = ParamOverride

# the public topology summary name must remain available so existing integrations keep resolving the canonical implementation
TopologySummary = TopologyCounts

# the public vector2 name must remain available so existing integrations keep resolving the canonical implementation
Vector2 = PlaneVector

# the public vector3 name must remain available so existing integrations keep resolving the canonical implementation
Vector3 = SpaceVector

# the public frozen mapping name must remain available so existing integrations keep resolving the canonical implementation
frozen_mapping = FreezeMapping

BindFunctionMut(
    FreezeMapping,
    __name__,
    "frozen_mapping",
    {
        "value": "Mapping[str, Any] | None",
        "return": "Mapping[str, Any]",
    },
    FuncSig(
        (
            FuncParam(
                "value",
                FuncParam.POSITIONAL_OR_KEYWORD,
                default=None,
                annotation="Mapping[str, Any] | None",
            ),
        ),
        return_annotation="Mapping[str, Any]",
    ),
    globals(),
)

# legacy module exports stay explicit so integrations cannot depend on implementation details
__all__ = (
    "BooleanOperation",
    "BoundingBox",
    "CadSource",
    "Capability",
    "Configuration",
    "ConstraintKind",
    "Diagnostic",
    "Expression",
    "FeatureKind",
    "GeometryKind",
    "JsonScalar",
    "JsonValue",
    "Parameter",
    "ParameterOverride",
    "ParameterRole",
    "ParameterValue",
    "Provenance",
    "ProvenanceSpan",
    "Severity",
    "Transform",
    "UnitSystem",
    "ValueKind",
    "Vector2",
    "Vector3",
    "frozen_mapping",
)
