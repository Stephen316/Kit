# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from typing import Mapping as TypeMap

# historical brep identity set 1 keeps pickle globals stable after module splits
KLegacyBrepOne: TypeMap[str, tuple[str, str]] = {
    "BrepEntity": ("BrepEntity", "interchange.brep"),
    "BrepCurve": ("BrepCurve", "interchange.brep"),
    "LineCurve": ("LineCurve", "interchange.brep"),
    "CircleCurve": ("CircleCurve", "interchange.brep"),
    "EllipseCurve": ("EllipseCurve", "interchange.brep"),
    "NurbsCurve": ("NurbsCurve", "interchange.brep"),
    "IntersectCurve": ("IntersectionCurve", "interchange.brep"),
    "NativeCurve": ("NativeCurve", "interchange.brep"),
    "BrepPcurve": ("BrepPcurve", "interchange.brep"),
    "LinePcurve": ("LinePcurve", "interchange.brep"),
    "CirclePcurve": ("CirclePcurve", "interchange.brep"),
    "NurbsPcurve": ("NurbsPcurve", "interchange.brep"),
    "NativePcurve": ("NativePcurve", "interchange.brep"),
    "BrepSurface": ("BrepSurface", "interchange.brep"),
    "PlaneSurface": ("PlaneSurface", "interchange.brep"),
    "CylinderSurface": ("CylinderSurface", "interchange.brep"),
    "ConeSurface": ("ConeSurface", "interchange.brep"),
    "SphereSurface": ("SphereSurface", "interchange.brep"),
    "TorusSurface": ("TorusSurface", "interchange.brep"),
    "NurbsSurface": ("NurbsSurface", "interchange.brep"),
    "OffsetSurface": ("OffsetSurface", "interchange.brep"),
    "NativeSurface": ("NativeSurface", "interchange.brep"),
    "BrepVertex": ("BrepVertex", "interchange.brep"),
    "BrepEdge": ("BrepEdge", "interchange.brep"),
}
