# SOLIDWORKS archive plane references

The packaged archive cursor shares scalar bounds, finite coordinate checks, text framing and map allocations across the sketch and resolved replay paths. The typed principal reference reader follows `moCompRefPlane_c` through the allocated local unit and part object to the saved feature ID, axis code and transform. Both the Origin profile and authored rectangle profiles use that route.

The principal datum reader gets the origin and world normal directly from `moDefaultRefPlnData_c`. Its preceding atom and reference-geometry fields share the typed reader used by the P04 embedded plane. The native pointer observer retains the compact null events when a packaged reader consumes them.

The P01 and P03 rectangle reports and the P04 resolved, face occurrence and sketch reports retain their recorded SHA-256 digests. The next integration step connects the typed datum and reference records through the production support path. [SOLIDWORKS resolved replay](SolidWorksResolvedEntry.md), [rectangular plane evidence](SolidWorksRectangularPlaneEvidence.md)
