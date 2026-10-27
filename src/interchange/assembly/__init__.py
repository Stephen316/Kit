# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

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
from interchange.compatibility.PythonCompat import BindCompatMut
from interchange.compatibility.PythonCompatAssemblyMethods import BindAssemblyMut
from interchange.compatibility.PublicMetadata import BindModules
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

ComponentDefinition = ComponentDef
ComponentDocument = ComponentDoc
ComponentInstance = ComponentInst
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
