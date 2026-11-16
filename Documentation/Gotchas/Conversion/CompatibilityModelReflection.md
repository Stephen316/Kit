# Compatibility metadata differs from canonical model storage

## Expectation

Typed semantic projection must classify records and field relationships using their stable model identities.

## Observed behavior

The interchange compatibility installer changes class `__name__`, `__dataclass_fields__` and reflected field names to their historical public forms.
For example, the original `RefPlaneFeature` can appear as `ReferencePlaneFeature`, while a typed parameter slot can expose a snake-case reflected name.
Using those reflected spellings directly bypasses canonical reference and quantity maps.
Source inspection of [PythonCompat.py](../../../src/interchange/Compatibility/PythonCompat.py) established this behavior.

## Workaround

Use `CanonName` for model classification.
Resolve each reflected field through `ResolveField` before accessing canonical storage or applying semantic roles.
Use `GetSlotNames` for collision checks against actual storage fields.
The comparator uses these existing repository contracts without changing public reflection or wire serialization.

The [comparison process coverage](../../../tests/Research/Archives/Comparison/SemanticComparisonTests.py) exercises independent identities, storage order and typed parameter bindings.
Hosted execution remains required; no local comparison or test execution was performed.
