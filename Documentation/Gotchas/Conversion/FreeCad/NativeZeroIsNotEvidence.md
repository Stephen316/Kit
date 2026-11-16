# Native zero defaults are not saved scalar evidence

A matching spreadsheet literal is expected to corroborate the native property's saved numeric value before a typed dependency is assigned.
The native reader's [`RemainingMut`](../../../../src/convert/adapters/freecad/Native.py) instead creates zero-valued placeholders for unconsumed expression paths, preserving the path and expression without decoding that property's current scalar.
Its `Number` and `Integer` readers also default missing, malformed or nonfinite scalar text to zero.
An expression attached to a nonzero placement coordinate or a `Float value="nan"` can therefore appear to match a zero alias despite having no valid saved scalar equality.

The [alias recovery](../../../Changes/FreeCad/FreeCadNativeSheetAliases.md) requires actual supported scalar-property or indexed dimensional-constraint evidence, validates the raw numeric domain and expected native kind/unit, and checks exact agreement with the parsed parameter before comparing physical quantities.
Synthetic placeholders and invalid raw scalars remain unresolved with `unverified_native_value`; their original expression, normalized reader value and raw metadata remain inspectable.
This does not change the general native parser, prove recomputation, or establish native acceptance.

Source-authored public process controls cover a saved placement coordinate of 17 with a zero-alias expression placeholder, plus nonfinite, invalid and missing raw `Factor` values with a zero alias.
They require unresolved dependency IDs, retained raw evidence and byte-identical unchanged-native replay.
These controls are authored XML, not a witnessed discrepant edit saved by FreeCAD; local verification is static only.
