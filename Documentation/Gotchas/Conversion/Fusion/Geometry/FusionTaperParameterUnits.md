# Fusion taper display units differ from numeric storage

An extrusion's taper parameter advertises the unit `deg` and stores expressions such as `7 deg`, but its persistent numeric value is radians. The corresponding `DcDoubleParameter.value` also stores radians. Copying the degree number into either numeric field makes the persisted feature disagree with its expression and cached geometry.

The lower radius is the sketch radius. With positive-Z extrusion height `h`, the upper radius is `r + h * tan(angleRadians)`: a positive taper expands the top. The cone carrier stores sine and cosine of that angle, while its dimensional parameter scale remains independent of the upper radius. No separate Draft feature is required for an ordinary tapered extrusion.

The authoring API accepts degrees explicitly and converts both parameter values to radians. It derives the top radius, cone history and analytic cache from that same angle. A nonzero angle whose radius change disappears at floating-point precision is rejected, as are angles at or beyond ±90° and nonpositive resulting top radii.

The [controlled Design decode](../../../../../re/Fusion/Reconstruction/TaperedHistory/ControlledDesign.json) records the native 7° parameter value `0.12217304763960307`, and the [controlled history](../../../../../re/Fusion/Reconstruction/TaperedHistory/ControlledHistory.json) records sine `0.12186934340514748` and cosine `0.992546151641322`. See [the complete authoring feature](../../../../Changes/Fusion/FusionTaperedDocuments.md) for usage and current acceptance evidence.
