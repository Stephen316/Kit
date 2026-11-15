# SOLIDWORKS archive plane references

The packaged archive cursor shares scalar bounds, finite coordinate checks, text framing and map allocations across the sketch and resolved replay paths. The typed principal reference reader follows `moCompRefPlane_c` through the allocated local unit and part object to the saved feature ID, axis code and transform. Both the Origin profile and authored rectangle profiles use that route.

The P01 and P03 rectangle reports and the P04 resolved reports retain their recorded SHA-256 digests. The packaged fields are ready for a source-only configuration and resolved walk. The public adapter still uses its existing support resolution path. [SOLIDWORKS resolved replay](SolidWorksResolvedEntry.md), [rectangular plane evidence](SolidWorksRectangularPlaneEvidence.md)
