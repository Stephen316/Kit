# Equal extrusion distances do not establish symmetry

## Expectation

Native `Part::Extrusion` reading preserves the saved end-mode and reversal flags independently of its numeric distances.

## Observed behavior

The earlier reader inferred symmetry when positive `LengthFwd` and `LengthRev` were equal and always returned `reversed=False`.
A native 7/7 mm two-ended extrusion with `Symmetric=false` therefore became a symmetric extrusion in the neutral record.
A saved symmetric 16/0 mm extrusion lost its symmetry flag.
The [official FreeCAD 1.0.2 parameter computation](https://github.com/FreeCAD/FreeCAD/blob/1.0.2/src/Mod/Part/App/FeatureExtrusion.cpp#L225-L237) distinguishes these cases: symmetry uses the forward distance as total thickness and ignores reverse distance.
Reversal acts independently on the direction.

## Workaround

Read the saved Boolean `Symmetric` and `Reversed` properties through the existing property reader.
Keep both raw distances and the direction vector, including inactive reverse values.
The [reader repair](../../../Changes/FreeCad/FreeCadNativeEndSemantics.md) retains the existing termination convention and native-property metadata.
Its native-only process fixtures omit both neutral-manifest representations so the public read must exercise native decoding.
Local tests were not run; hosted process and native application acceptance remain separate evidence requirements.
