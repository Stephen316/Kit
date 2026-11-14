# Named metadata can be typed by a value class GUID

## Expectation

A named metadata entry has an intrinsic metatype, a reference metatype, `Vector`, or one of the named types in the catalog.

## Actual behavior

Entity frames of `DcExtrudeFeature`, `DcPCBBaseBody` and `DcPCBExtrude` records in `example1.f3z` name the type `EA46307F-1FD6-4B11-9C97-353B74F5E413`. This is the GUID of the value class `VisualMaterialValue`. The reader raised `Unsupported Fusion entity named metadata metatype`.

All five entries decode to the exact record end as value objects of that class.

## Workaround

When a type name is not a named type, look it up as a class GUID in the profile. If it is a value class, read one value object of that class. The vector element name follows the same rule.

## Evidence

- [Read gap notes](../../../../../re/Fusion/Reconstruction/ReadGaps/ReadGapNotes.md#example-record-rules)
- [Named type trial](../../../../../re/Fusion/Reconstruction/ReadGaps/TryNamed.py)
