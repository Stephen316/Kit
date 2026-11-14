# Typed subtype fields must keep the stream order

## Expectation

A typed subtype body is a frozen dataclass with named fields. A reader can expect that the field order is free, as in other records.

## Actual behavior

The typed bodies in `Complex/Typed` replace the positional grammar tree of eleven subtypes. `TypeBody` converts a tree to a record after reading. `TreeBody` converts the record back to a tree before emission.

`WalkSubtypes`, `MapSubtypes` and `RelinkSubtypes` read a record through `dataclasses.fields`. They visit the fields in declaration order. The subtype table numbers each inline definition in stream pre-order. The two orders agree only when the field order follows the stream order.

| Rule | Result of a violation |
| --- | --- |
| Field order follows the stream order of the record | `RelinkSubtypes` counts nested definitions in a different order than the table |
| A typed subtype name carries its record class | `TreeBody` raises `ValueError` before emission |
| A variant field agrees with its key | The record converter raises `ValueError` |

Some grammar items have no field. A fixed token, such as the cross-section enum `0` of `srf_srf_v_bl_spl_sur`, comes from the converter. The branch key of the `context` and `tail` rules is always `0`. The converter also supplies that key.

## Workaround

Declare a new field at its stream position. Keep each subtype-bearing field, such as a surface or curve record, in the order it appears in the stream. Construct a `SubtypeNode` for a typed subtype name with its record class, not with a tuple.

## Evidence

- [Typed verification](../../../../../re/Fusion/Reconstruction/ComplexGeometry/TypedFields/TypedVerify.json)
- Remote integration cases `TestRecordWalk` and `TestPositional` in `TypedFieldTests.py`
