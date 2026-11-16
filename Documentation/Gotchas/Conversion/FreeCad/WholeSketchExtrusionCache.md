# The native extrusion base is the whole sketch

A declared closed-profile roster does not alone identify every entity used by native `Part::Extrusion`.
The emitted `Base` link points to the whole sketch.
An extra nonconstruction loop can therefore change the native result even when it is absent from the declared roster.

The [initial-cache guard](../../../Changes/FreeCad/FreeCadInitialExtrusionShapes.md) requires one supported closed loop containing every nonconstruction entity, matching geometry kinds and no feature selections.
Unsupported or ambiguous geometry receives no new cache; no subset solid stands in for the live feature.
The process coverage includes an undeclared extra circle and verifies that it acquires no cache.
Local verification remains static; hosted and native initial-open evidence remain required.
