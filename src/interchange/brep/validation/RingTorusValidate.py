from math import isfinite as IsFinite

from interchange.brep.surfaces.BrepSurfaces import TorusSurface
from interchange.brep.validation.BrepRoundFrame import IsRoundFrame


# a regular torus without a trim boundary must be a nonsingular ring
def IsRingTorus(Surface: TorusSurface) -> bool:
    return (
        IsFinite(Surface.major_radius)
        and IsFinite(Surface.minor_radius)
        and Surface.major_radius > Surface.minor_radius > 0.0
        and IsRoundFrame(Surface.center, Surface.axis, Surface.reference_direction)
    )
