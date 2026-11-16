# A sketch reference can have no operation definition

## Expectation

A missing feature definition identifies a timeline operation whose required semantics remain uninterpreted.

## Observed behavior

The strict Fusion rectangle reader represents the declared sketch with a `reference` feature step whose `sketch_id` resolves to that sketch.
The step has no operation or definition; the following extrusion retains it as an input dependency.
The earlier reader inventory and graph projection unconditionally reported this representation as `missing_feature_definition`.
Stephen316 identified the false finding in [sealed P03 controller observations](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6928157508).

## Workaround

The [sketch-reference recognition](../../../Changes/Research/Readers/Comparison/SemanticSketchReferences.md) requires an actual reference kind, no operation and a unique declared root typed sketch target.
It retains sketch and timeline dependencies, native evidence and unrelated unresolved findings.
Operation-bearing references, unknown kinds, missing or ambiguous targets and nested metadata cannot satisfy this exception.
The recognition does not qualify a source inventory or native conversion.
Local tests were not run; hosted process checks and independent semantic acceptance remain required.
