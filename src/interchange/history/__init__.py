from dataclasses import dataclass as DataClass
from inspect import Signature as FuncSig

from interchange.enums.EnumDocument import Capability
from interchange.features.FeatureBody import DesignBody
from interchange.features.FeatureContract import FeatureDef
from interchange.features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.features.FeatureKinds import (
    ChamferFeature,
    CirclePattern,
    CombineFeature,
    DomeFeature,
    FilletFeature,
    HoleFeature,
    LinearPattern,
    MoveBodyFeature,
    NativeFeature,
    RefPlaneFeature,
    RevolveFeature,
    ScaleFeature,
    ShellFeature,
)
from interchange.features.FeatureStep import FeatureCfgState, FeatureStep
from interchange.payloads.PayloadRecord import BrepPayload
from interchange.payloads.PayloadRoles import PayloadRole
from interchange.core.ModelBase import ModelBase
from interchange.compatibility.PythonCompat import BindCompatMut
from interchange.compatibility.PythonCompatHistoryMethods import BindHistoryMut
from interchange.records.RecordTopology import TopologyCounts

# one shared empty set keeps capability defaults free of repeated constructor calls
KEmptyCaps: frozenset[Capability] = frozenset()


# adapter capability sets centralize feature support checks for conversion decisions
@DataClass(frozen=True, slots=True)
class AdapterCaps(ModelBase):
    Values: frozenset[Capability] = KEmptyCaps

    # callers need one consistent containment check for adapter support declarations
    def HasCapability(self, CapabilityValue: Capability) -> bool:
        return CapabilityValue in self.Values

    # lowercase reads and the historical method alias stay real runtime members
    @property
    def values(self) -> frozenset[Capability]:
        return self.Values

    supports = HasCapability


BindCompatMut(
    (
        FeatureCfgState,
        ExtrudeFeature,
        FilletFeature,
        RevolveFeature,
        HoleFeature,
        ChamferFeature,
        ShellFeature,
        LinearPattern,
        CirclePattern,
        RefPlaneFeature,
        DomeFeature,
        MoveBodyFeature,
        CombineFeature,
        ScaleFeature,
        NativeFeature,
        FeatureStep,
        TopologyCounts,
        DesignBody,
        BrepPayload,
        AdapterCaps,
    ),
    {__name__: globals()},
)
BindHistoryMut(AdapterCaps)

for FeatureAttrName, FeatureAttrValue in {
    "__name__": "ExtrusionEndCondition",
    "__qualname__": "ExtrusionEndCondition",
    "__module__": __name__,
}.items():
    setattr(ExtrudeEnd, FeatureAttrName, FeatureAttrValue)
for PayloadAttrName, PayloadAttrValue in {"__module__": __name__}.items():
    setattr(PayloadRole, PayloadAttrName, PayloadAttrValue)
for DefinitionAttrName, DefinitionAttrValue in {
    "__name__": "FeatureDefinition",
    "__qualname__": "FeatureDefinition",
    "__module__": __name__,
    "__signature__": FuncSig(),
}.items():
    setattr(FeatureDef, DefinitionAttrName, DefinitionAttrValue)
for TopologyAttrName, TopologyAttrValue in {"__module__": __name__}.items():
    setattr(TopologyCounts, TopologyAttrName, TopologyAttrValue)

# the public extrusion end condition name must remain available so existing integrations keep resolving the canonical implementation
ExtrusionEndCondition = ExtrudeEnd

# the public feature definition name must remain available so existing integrations keep resolving the canonical implementation
FeatureDefinition = FeatureDef

# the public topology summary name must remain available so existing integrations keep resolving the canonical implementation
TopologySummary = TopologyCounts

# the public adapter capabilities name must remain available so existing integrations keep resolving the canonical implementation
AdapterCapabilities = AdapterCaps

# the public body name must remain available so existing integrations keep resolving the canonical implementation
Body = DesignBody

# the public circular pattern feature name must remain available so existing integrations keep resolving the canonical implementation
CircularPatternFeature = CirclePattern

# the public extrusion feature name must remain available so existing integrations keep resolving the canonical implementation
ExtrusionFeature = ExtrudeFeature

# the public feature configuration state name must remain available so existing integrations keep resolving the canonical implementation
FeatureConfigurationState = FeatureCfgState

# the public linear pattern feature name must remain available so existing integrations keep resolving the canonical implementation
LinearPatternFeature = LinearPattern

# the public native feature definition name must remain available so existing integrations keep resolving the canonical implementation
NativeFeatureDefinition = NativeFeature

# the public reference plane feature name must remain available so existing integrations keep resolving the canonical implementation
ReferencePlaneFeature = RefPlaneFeature

# the public revolution feature name must remain available so existing integrations keep resolving the canonical implementation
RevolutionFeature = RevolveFeature


# legacy module exports stay explicit so integrations cannot depend on implementation details
__all__ = (
    "AdapterCapabilities",
    "Body",
    "BrepPayload",
    "ChamferFeature",
    "CircularPatternFeature",
    "CombineFeature",
    "DomeFeature",
    "ExtrusionEndCondition",
    "ExtrusionFeature",
    "FeatureConfigurationState",
    "FeatureDefinition",
    "FeatureStep",
    "FilletFeature",
    "HoleFeature",
    "LinearPatternFeature",
    "MoveBodyFeature",
    "NativeFeatureDefinition",
    "PayloadRole",
    "ReferencePlaneFeature",
    "RevolutionFeature",
    "ScaleFeature",
    "ShellFeature",
    "TopologySummary",
)
