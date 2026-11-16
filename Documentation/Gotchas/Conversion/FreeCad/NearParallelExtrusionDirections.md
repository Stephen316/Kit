# A near-unit dot product does not prove parallel extrusion

A small transverse direction component changes the dot product only quadratically.
A cosine tolerance near one can therefore admit an oblique direction while an axis-aligned prism cache ignores its transverse displacement.

The [initial-cache guard](../../../Changes/FreeCad/FreeCadInitialExtrusionShapes.md) first requires exact cross-product collinearity, then verifies normal alignment and finite end values.
It conservatively omits the cache when floating coordinates cannot satisfy that restriction.
The original native direction remains unchanged, and no new acceptance assertion follows from omission or cache presence.
A public process control supplies a `1e-5` transverse component and requires no cache.
No local process or native execution was performed; hosted and native verification remain required.
