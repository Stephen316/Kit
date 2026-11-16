from interchange.Compatibility.PythonCompatAnnots import KPythonCompatAnnots
from interchange.Compatibility.PythonCompatModelsApiOne import KLegacyApiOne
from interchange.Compatibility.PythonCompatModelsApiTwo import KLegacyApiTwo
from interchange.Compatibility.PythonCompatModelsBrepOne import KLegacyBrepOne
from interchange.Compatibility.PythonCompatModelsBrepTwo import KLegacyBrepTwo
from interchange.Compatibility.PythonCompatModelsCore import KLegacyCore

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
