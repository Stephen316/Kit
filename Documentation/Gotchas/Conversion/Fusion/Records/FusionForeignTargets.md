# Cross-document references can name a class that the document lacks

## Expectation

The reference check can follow the target class lineage in the document profile. A reference whose target does not derive from the member type is invalid.

## Actual behavior

`JointOccurrence.rAssyConstr` in `example1.f3z` holds a cross-document reference. Its type GUID `7F5A0426` is `Joint`, which derives from `AssyConstraint` `B96995C7`. The member type asks for `AssyConstraint`. `Joint` lives in the other document, so the referring document's profile has no schema for it. The check stopped at the unknown class and raised `Fusion entity reference target class is incompatible`.

## Workaround

Follow the target lineage only for classes that the profile defines. A cross-document target of a foreign class keeps its stated type GUID. Local and segment references keep the full check, because their classes are always in the profile.

## Evidence

- [Read gap notes](../../../../../re/Fusion/Reconstruction/ReadGaps/ReadGapNotes.md#example-record-rules)
- [Reference spy](../../../../../re/Fusion/Reconstruction/ReadGaps/RefSpy.py)
