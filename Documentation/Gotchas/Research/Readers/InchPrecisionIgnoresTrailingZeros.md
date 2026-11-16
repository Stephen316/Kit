# Inch precision ignores trailing zeros

## Expectation

A fixture containing `0.040` can appear to exercise rejection of three fractional digits at a two-digit display precision.

## Actual behavior

The existing [inch decimal parser](../../../../src/convert/adapters/solidworks/Core/InchDecimal.py) removes trailing zeros before counting fractional digits.
It counts `0.040` as two significant fractional digits and `0.041` as three.
The first indexed-binding ambiguity fixture incorrectly expected the trailing-zero form to remain unresolved.
The remote parser-process case instead reported its valid `1.0 mm` binding.
The one- and 256-dimension roster cases passed in the same run.
[Failure evidence](https://github.com/TryUniCAD/Kit/actions/runs/43668887044/job/132674284143)

## Workaround

Use a third nonzero digit to exercise excess-precision rejection.
Keep a separate positive trailing-zero case to preserve the existing reader contract.
The repaired fixture retains unresolved assertions and adds dimension-specific scalar diagnostics.
It does not change the production parser, binding proof, or rounding tolerance.
See [the indexed-binding change entry](../../../Changes/Research/Readers/IndexedInchScalarBinding.md).
