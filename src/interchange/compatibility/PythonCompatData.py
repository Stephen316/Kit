# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from interchange.compatibility.PythonCompatAnnots import KPythonCompatAnnots
from interchange.compatibility.PythonCompatModelsApiOne import KLegacyApiOne
from interchange.compatibility.PythonCompatModelsApiTwo import KLegacyApiTwo
from interchange.compatibility.PythonCompatModelsBrepOne import KLegacyBrepOne
from interchange.compatibility.PythonCompatModelsBrepTwo import KLegacyBrepTwo
from interchange.compatibility.PythonCompatModelsCore import KLegacyCore

# split identity registries combine here so installers consume one immutable contract
KLegacyModels = {
    **KLegacyCore,
    **KLegacyBrepOne,
    **KLegacyBrepTwo,
    **KLegacyApiOne,
    **KLegacyApiTwo,
}

# split annotation registries combine here so reflection installation remains declarative
KLegacyAnnots = KPythonCompatAnnots

# brep entities inherited shared metadata ahead of specific fields unlike every later package
KBrepLeadTopologyNames = (
    "BrepVertex",
    "BrepEdge",
    "BrepCoedge",
    "BrepLoop",
    "BrepWire",
    "BrepFace",
    "BrepFaceUse",
    "BrepShell",
    "BrepShellUse",
    "BrepRegion",
    "BrepBody",
)

# brep geometry entities share the same historical metadata leading layout
KBrepLeadGeometryNames = (
    "LineCurve",
    "CircleCurve",
    "EllipseCurve",
    "NurbsCurve",
    "IntersectCurve",
    "NativeCurve",
    "LinePcurve",
    "CirclePcurve",
    "NurbsPcurve",
    "NativePcurve",
    "PlaneSurface",
    "CylinderSurface",
    "ConeSurface",
    "SphereSurface",
    "TorusSurface",
    "NurbsSurface",
    "OffsetSurface",
    "NativeSurface",
)

# brep entities inherited shared metadata ahead of specific fields unlike every later package
KLeadingMetadataModels = frozenset(KBrepLeadTopologyNames + KBrepLeadGeometryNames)
