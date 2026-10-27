# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from interchange.brep.curves.BrepCurves import (
    BrepCurve,
    BrepEntity,
    CircleCurve,
    EllipseCurve,
    IntersectCurve,
    LineCurve,
    NativeCurve,
    NurbsCurve,
)
from interchange.brep.topology.BrepModel import BrepModel
from interchange.brep.curves.BrepPcurves import (
    BrepPcurve,
    CirclePcurve,
    LinePcurve,
    NativePcurve,
    NurbsPcurve,
)
from interchange.brep.surfaces.BrepSurfaces import (
    BrepSurface,
    ConeSurface,
    CylinderSurface,
    NativeSurface,
    NurbsSurface,
    OffsetSurface,
    PlaneSurface,
    SphereSurface,
    TorusSurface,
)
from interchange.brep.topology.BrepTopology import (
    BrepBody,
    BrepCoedge,
    BrepEdge,
    BrepFace,
    BrepFaceUse,
    BrepLoop,
    BrepRegion,
    BrepShell,
    BrepShellUse,
    BrepVertex,
    BrepWire,
)
from interchange.compatibility.PythonCompat import BindCompatMut
from interchange.compatibility.PythonCompatBrepMethods import BindBrepMut

BindCompatMut(
    (
        LineCurve,
        CircleCurve,
        EllipseCurve,
        NurbsCurve,
        IntersectCurve,
        NativeCurve,
        LinePcurve,
        CirclePcurve,
        NurbsPcurve,
        NativePcurve,
        PlaneSurface,
        CylinderSurface,
        ConeSurface,
        SphereSurface,
        TorusSurface,
        NurbsSurface,
        OffsetSurface,
        NativeSurface,
        BrepVertex,
        BrepEdge,
        BrepCoedge,
        BrepLoop,
        BrepWire,
        BrepFace,
        BrepFaceUse,
        BrepShell,
        BrepShellUse,
        BrepRegion,
        BrepBody,
        BrepModel,
    ),
    {__name__: globals()},
)
BindBrepMut(BrepModel)

IntersectionCurve = IntersectCurve

# brep consumers need one intentional historical public contract
__all__ = (
    "BrepBody",
    "BrepCoedge",
    "BrepCurve",
    "BrepEdge",
    "BrepEntity",
    "BrepFace",
    "BrepFaceUse",
    "BrepLoop",
    "BrepModel",
    "BrepPcurve",
    "BrepRegion",
    "BrepShell",
    "BrepShellUse",
    "BrepSurface",
    "BrepVertex",
    "BrepWire",
    "CircleCurve",
    "CirclePcurve",
    "ConeSurface",
    "CylinderSurface",
    "EllipseCurve",
    "IntersectionCurve",
    "LineCurve",
    "LinePcurve",
    "NativeCurve",
    "NativePcurve",
    "NativeSurface",
    "NurbsCurve",
    "NurbsPcurve",
    "NurbsSurface",
    "OffsetSurface",
    "PlaneSurface",
    "SphereSurface",
    "TorusSurface",
)
