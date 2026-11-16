from interchange.assembly.AssemblyData import AssemblyData
from interchange.assembly.AssemblyEnums import (
    ComponentKind,
    MateAlignment,
    MateEntityKind,
    MateKind,
)
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentDocument import ComponentDoc
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.assembly.MateConstraint import MateConstraint
from interchange.assembly.MateEntity import MateEntity
from interchange.assembly.MateGroup import MateGroup
from interchange.Compatibility.PythonCompat import BindCompatMut
from interchange.Compatibility.PythonCompatAssemblyMethods import BindAssemblyMut
from interchange.Compatibility.PublicMetadata import BindModules
from interchange.assembly.TransformMatrix import TransformMatrix

BindModules((ComponentKind, MateAlignment, MateEntityKind, MateKind), __name__)

BindCompatMut(
    (
        TransformMatrix,
        ComponentDoc,
        ComponentDef,
        ComponentInst,
        MateEntity,
        MateConstraint,
        MateGroup,
        AssemblyData,
    ),
    {__name__: globals()},
)
BindAssemblyMut(AssemblyData, TransformMatrix)

# the public component definition name must remain available so existing integrations keep resolving the canonical implementation
ComponentDefinition = ComponentDef

# the public component document name must remain available so existing integrations keep resolving the canonical implementation
ComponentDocument = ComponentDoc

# the public component instance name must remain available so existing integrations keep resolving the canonical implementation
ComponentInstance = ComponentInst

# the public matrix4 name must remain available so existing integrations keep resolving the canonical implementation
Matrix4 = TransformMatrix

# assembly consumers need one intentional historical public contract
__all__ = (
    "AssemblyData",
    "ComponentDefinition",
    "ComponentDocument",
    "ComponentInstance",
    "ComponentKind",
    "MateAlignment",
    "MateConstraint",
    "MateEntity",
    "MateEntityKind",
    "MateGroup",
    "MateKind",
    "Matrix4",
)
