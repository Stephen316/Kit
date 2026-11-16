# FreeCAD native extrusion end semantics

The native `Part::Extrusion` reader now takes `Symmetric` and `Reversed` from their saved Boolean properties through the existing property reader.
Equal forward and reverse distances no longer imply symmetry, and an explicit reversal is retained.
Missing flags retain their existing false defaults.

The [official FreeCAD 1.0.2 implementation](https://github.com/FreeCAD/FreeCAD/blob/1.0.2/src/Mod/Part/App/FeatureExtrusion.cpp#L121-L130) treats the reverse length as an additional extrusion against the direction.
`Symmetric` instead uses the forward length as the total thickness and ignores the reverse length.
Its [parameter computation](https://github.com/FreeCAD/FreeCAD/blob/1.0.2/src/Mod/Part/App/FeatureExtrusion.cpp#L225-L237) applies reversal independently and halves the forward total only in symmetric mode.
Consequently, 7 mm forward and 7 mm reverse with `Symmetric=false` differs from a symmetric 7 mm total.

The reader preserves both raw distance properties, including an inactive nonzero reverse distance in symmetric mode, and the original direction vector.
It retains the existing blind termination convention: explicit distance fields and Boolean flags carry the mode, as in the existing native extrusion model contract.
No new end condition is inferred from equal numbers, no inactive value is replaced, and the raw native properties remain in the feature attributes.
This repair does not change spreadsheet reconciliation, parameter end ownership, writer admission or unsupported-feature guards.

## Process coverage and evidence

The new process cases construct independent native-only FCStd archives and invoke the public `OpenDocument` route in a separate Python process.
Fixtures contain only `Document.xml`: neither a ZIP Kit manifest nor its embedded XML representation can bypass native decoding.
The cases distinguish 7/7 mm separate ends, 16/0 mm symmetric total thickness, equal symmetric ends, explicit reversal, unequal ends, an inactive reverse value and absent flags.
They check both typed lengths and units, the original direction, source SHA-256, unmodified input bytes and raw saved flags.
Each report remains an unqualified reader observation with native application acceptance unestablished.

Pinned formatting, type, steering, path, rationale, binary-range and whitespace checks validate the implementation statically.
No local tests, collection, reproductions, CLI commands or CAD application runs were executed.
Hosted process execution remains required.
This change establishes no native edit, rebuild, save or fresh-reopen acceptance and does not qualify any source pair.
