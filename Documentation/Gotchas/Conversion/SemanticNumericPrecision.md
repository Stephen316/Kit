# Semantic normalization must preserve integer precision

## Expectation

Changing an integer control by one remains observable even when its magnitude exceeds floating-point integer precision.
Unit normalization must not collapse distinct scalar observations before applying the declared tolerance.

## Observed behavior

The initial A06 projection multiplied numeric quantities by a floating-point scale, including the identity scale `1.0`.
That conversion can map the integers `9007199254740992` and `9007199254740993` to the same float.
It also changed dimensionless integer controls into floats, allowing a floating tolerance to hide their difference.
Source inspection identified these paths; no local comparison experiment was run.

## Workaround

The comparator preserves integral normalized values and retains a reduced exact ratio for quantity arithmetic.
The ratio uses the canonical decimal magnitude and the finite unit-conversion factor.
The displayed normalized float does not replace that ratio.
Dimensional tolerances compare ratios, and dimensionless integer controls remain exact.

The sealed JSON boundary also refuses decimal literals that the existing codec would round to a different canonical decimal magnitude, including underflow.
The shared wire codec remains unchanged.

The [change entry](../../Changes/Research/Readers/Comparison/SemanticGraphComparison.md) links the command and its limits.
Process coverage includes large adjacent integers, permissive floating tolerances, small physical unit conversions and refused rounded literals.
Hosted execution remains required.
