# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from typing import TypeAlias

from interchange.geometry.models.GeometryConics import (
    ArcEllipseGeom,
    ArcHyperGeom,
    ArcParabGeom,
    EllipseGeometry,
    HyperbolaGeom,
    ParabolaGeom,
)
from interchange.geometry.models.GeometryCurves import (
    ArcGeometry,
    CircleGeometry,
    LineGeometry,
    NativeGeometry,
    PointGeometry,
    SplineGeometry,
)

# exhaustive geometry typing prevents new classes from escaping sketch validation
KGeometryTypes: TypeAlias = (  # lgtm[py/unused-global-variable]
    PointGeometry
    | LineGeometry
    | CircleGeometry
    | ArcGeometry
    | EllipseGeometry
    | ArcEllipseGeom
    | HyperbolaGeom
    | ArcHyperGeom
    | ParabolaGeom
    | ArcParabGeom
    | SplineGeometry
    | NativeGeometry
)
