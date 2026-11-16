from interchange.geometry.Models.GeometryConics import (
    ArcEllipseGeom,
    ArcHyperGeom,
    ArcParabGeom,
    EllipseGeometry,
    HyperbolaGeom,
    ParabolaGeom,
)
from interchange.geometry.Models.GeometryCurves import (
    ArcGeometry,
    CircleGeometry,
    LineGeometry,
    NativeGeometry,
    PointGeometry,
    SplineGeometry,
)
from interchange.geometry.Models.GeometryTypes import KGeometryTypes
from interchange.Compatibility.PythonCompat import BindCompatMut
from interchange.geometry.Models.Selection import Selection, SelectPathElem
from interchange.geometry.Models.Sketch import (
    ConstraintRef,
    Sketch,
    SketchEntity,
    SketchRelation,
)
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector

# historical geometry typing remains available because consumers inspect union coverage
Geometry = KGeometryTypes

BindCompatMut(
    (
        PointGeometry,
        LineGeometry,
        CircleGeometry,
        ArcGeometry,
        EllipseGeometry,
        ArcEllipseGeom,
        HyperbolaGeom,
        ArcHyperGeom,
        ParabolaGeom,
        ArcParabGeom,
        SplineGeometry,
        NativeGeometry,
        SupportPlane,
        SketchEntity,
        ConstraintRef,
        SketchRelation,
        Sketch,
        SelectPathElem,
        Selection,
    ),
    {__name__: globals()},
)

# the public arc ellipse geometry name must remain available so existing integrations keep resolving the canonical implementation
ArcEllipseGeometry = ArcEllipseGeom

# the public arc hyperbola geometry name must remain available so existing integrations keep resolving the canonical implementation
ArcHyperbolaGeometry = ArcHyperGeom

# the public arc parabola geometry name must remain available so existing integrations keep resolving the canonical implementation
ArcParabolaGeometry = ArcParabGeom

# the public constraint reference name must remain available so existing integrations keep resolving the canonical implementation
ConstraintReference = ConstraintRef

# the public hyperbola geometry name must remain available so existing integrations keep resolving the canonical implementation
HyperbolaGeometry = HyperbolaGeom

# the public parabola geometry name must remain available so existing integrations keep resolving the canonical implementation
ParabolaGeometry = ParabolaGeom

# the public selection path element name must remain available so existing integrations keep resolving the canonical implementation
SelectionPathElement = SelectPathElem

# the public sketch constraint name must remain available so existing integrations keep resolving the canonical implementation
SketchConstraint = SketchRelation

# geometry consumers need one intentional historical public contract
__all__ = (
    "ArcEllipseGeometry",
    "ArcGeometry",
    "ArcHyperbolaGeometry",
    "ArcParabolaGeometry",
    "CircleGeometry",
    "ConstraintReference",
    "EllipseGeometry",
    "Geometry",
    "HyperbolaGeometry",
    "LineGeometry",
    "NativeGeometry",
    "ParabolaGeometry",
    "PointGeometry",
    "PlaneVector",
    "Selection",
    "SelectionPathElement",
    "Sketch",
    "SketchConstraint",
    "SketchEntity",
    "SplineGeometry",
    "SupportPlane",
    "SpaceVector",
)
