# Fusion geometry arrays persist capacity descriptors

## Expectation

A geometry value vector might appear to use the same count-and-elements layout as the ordinary entity reflection containers.

## Actual behavior

The AcGe serializers write logical length, physical length, and growth length before the logical elements. Unused capacity contributes no element bytes. NURBS knot vectors additionally begin with a double tolerance, while the interval follows the control-point array under a geometry-version condition. A line segment callback writes its start point and displacement, rather than two endpoints.

Treating capacity as data, inserting the definition getter's rationality flag, or interpreting the displacement as an endpoint corrupts later fields or produces incorrect geometry.

## Workaround and evidence

Dispatch by the declared callback metatype, and retain all three array descriptors. Consume exactly the logical element count, and qualify the geometry version. Use the documented start-plus-displacement line representation. [The callback model](../../../../re/Fusion/Reconstruction/EntityGraph/ExtendedCallbacks.md) links native `AcGeFileIO::outFields` excerpts and the 712-archive byte-accounting evidence.
