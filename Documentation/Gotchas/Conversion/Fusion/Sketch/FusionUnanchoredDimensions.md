# Driving lengths do not anchor a sketch

A horizontal and vertical driving dimension constrain lengths, but they do not necessarily fix a rectangle's position. The native controlled capture started with a 17×23 mm rectangle at the origin. After editing the corresponding user parameters to 19 and 29 mm, Fusion moved its lower edge to `y=-6 mm` while leaving its upper edge at `y=23 mm`.

The [capture report](../../../../../re/Fusion/LocalOracle/RectangleDimensions/Capture.json) records every endpoint before and after the edit. Both dimension values and their user-parameter bindings are correct, and the profile remains closed. The native `addTwoPointRectangle` control reports an empty geometric-constraint collection; the two linear dimensions appear in the separate dimension collection.

Preserve dimension orientation, endpoint order, user/model parameter binding and anchor constraints as separate semantics. Do not infer a fixed origin from the initial coordinates, or compare only dimensions when checking native regeneration. Independent authoring of an origin-anchored dimensioned rectangle needs explicit and accepted anchoring semantics.
