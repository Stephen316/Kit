# Fusion parameter writes do not regenerate saved geometry

Editing the numeric parameter, its expression, and its design-capture binding does not update the archive's BRep caches.
A file can load with the new parameter values while displaying the original cached solid.

In the controlled circular-extrusion experiment, Kit rewrote a 7 mm depth to 19 mm using its native parameter and binding serializers.
On import, Fusion reported the 19 mm parameter and retained both timeline entries, but the body still measured 7 mm high with volume 2.1991148575129498 cm³.
Only after `Design.computeAll()` did the body measure 19 mm high with volume 5.969026041820864 cm³.
A subsequent native edit to 23 mm, save, and reopen retained the rebuilt geometry.

This is evidence for same-source parametric editing followed by vendor rebuild.
It is not evidence that Kit independently generated the feature graph or BRep cache.
A complete native writer must emit consistent geometry, history state, topology references, and parameter values without requiring the CAD application at production runtime.

See the [rewrite provenance](../../../../re/Fusion/LocalOracle/Features/Rewrite.json) and [native acceptance record](../../../../re/Fusion/LocalOracle/Features/Acceptance.json).
