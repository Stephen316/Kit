# Extrusion flags remain independent of distances and direction

## Expectation

Native `Part::Extrusion` reading and writing preserve the saved end-mode and reversal flags independently of numeric distances and the base direction.

## Observed behavior

The earlier reader inferred symmetry when positive `LengthFwd` and `LengthRev` were equal and always returned `reversed=False`.
A native 7/7 mm two-ended extrusion with `Symmetric=false` therefore became a symmetric extrusion in the neutral record.
A saved symmetric 16/0 mm extrusion lost its symmetry flag.
The [official FreeCAD 1.0.2 parameter computation](https://github.com/FreeCAD/FreeCAD/blob/1.0.2/src/Mod/Part/App/FeatureExtrusion.cpp#L225-L237) distinguishes these cases: symmetry uses the forward distance as total thickness and ignores reverse distance.
Reversal acts independently on the direction.
The earlier inline writer absorbed reversal into an implicit profile normal but skipped that step for explicit directions, while always writing `Reversed=false`.
An explicit axis with `reversed=True` therefore lost reversal.

## Workaround

Read the saved Boolean `Symmetric` and `Reversed` properties through the existing property reader.
Keep both raw distances and the direction vector, including inactive reverse values.
The [reader repair](../../../Changes/FreeCad/FreeCadNativeEndSemantics.md) retains the existing termination convention and native-property metadata.
Its native-only process fixtures omit both neutral-manifest representations so the public read must exercise native decoding.
The [inline writer repair](../../../Changes/FreeCad/FreeCadReversedExtrusion.md) emits the normalized base direction and a separate reversal flag.
Its explicit false definition retains precedence over direction-multiplier and Cut fallbacks, while linked-edit seeds retain their existing effective vectors and default false flag.
The new public-write process fixtures inspect native properties and independently read an archive with only the neutral-manifest representations removed.
Local tests were not run; hosted process and native application acceptance remain separate evidence requirements.
