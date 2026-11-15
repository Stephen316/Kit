# Form inertia uses moments about the coordinate origin

## Expectation

A mass cache could store its inertia tensor about the center of mass after storing that center separately.
A symmetric example around the origin would not reveal a missing translation term.

## Actual behavior

`MassPropertyCacheValue.moi` uses second moments about the coordinate origin.
`MassPropertyCacheValue.moiOffDiag` uses negated second cross products in the same frame.
`cog` holds the center separately.
Centroid subtraction would therefore change the represented tensor instead of applying a format conversion.
The convention already appears in `CuboidCache` and `PartCache`.

## Workaround

Accumulate the second moments through the same divergence-theorem surface integral as the first moments.
Divide only the first moments by volume to obtain the center.
Do not subtract `volume * center * center` from second moments or `volume * center[a] * center[b]` from cross products.
Retain the translation terms in both tensors.
Validate an asymmetric off-origin case as well as centered controls.
The [native off-origin lifecycle](../../../../../../re/Fusion/LocalOracle/FormDocuments/General/CapAccept/NativeAcceptance.json) includes grips translated by `(13, -21, 42)` cm.
`getXYZMomentsOfInertia()` returns one success flag and six mass-weighted moments.
The oracle divides those moments by each body's physical density before comparing geometry across different materials.
`TestShiftMass` generates both compared archives through the current `EmitFormDoc` writer.
It checks the center translation and all six tensor components against the exact parallel-axis formula.
`TestCubeMass` independently constrains the absolute scale with a closed unit-cube BRep emitted and read through the complete document codec.
Its exact area, volume, center, diagonal inertia, and off-diagonal products prevent a shared scale error from passing the translation identity.
The archive round-trip also checks the recovered cage and converted body, rather than calling mass helpers as an isolated unit.

## Evidence

- [Origin-moment cache writer](../../../../../../src/convert/formats/Fusion/DocumentCodec/Form/CenteredMass.py)
- [Existing cuboid convention](../../../../../../src/convert/formats/Fusion/DocumentCodec/Rectangle/CuboidCache.py)
- [Existing feature convention](../../../../../../src/convert/formats/Fusion/DocumentCodec/PartFeatures/Design/PartCache.py)
- [Native acceptance](../../../../../../re/Fusion/LocalOracle/FormDocuments/General/CapAccept/NativeAcceptance.json)
