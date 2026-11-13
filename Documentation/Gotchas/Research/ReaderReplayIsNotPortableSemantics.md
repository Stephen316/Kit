# Reader replay evidence is not portable semantics

## Expectation

A validated neutral JSON document can appear to contain only decoded design information.
A JSON roundtrip can appear to establish that its full source meaning is understood.

## Actual behavior

The [SOLIDWORKS reader](../../../src/convert/adapters/solidworks/core/Adapter.py) retains source bytes in document metadata.
It can also read an embedded `Kit/Interchange` document instead of decoding independent native semantics.
Typed features can retain native termination codes or mappings without independent direction/frame qualification.
Model validation checks structural relationships, not complete source interpretation.

This behavior was identified through source inspection of `ReadAction`, `RetainSource` and `BuildExtrude`.
It does not establish a newly measured conversion defect.

## Workaround

Use the [research reader receipt](../../Reference/Research/SolidworksResearchReader.md) to retain unresolved evidence separately.
Reject embedded Kit documents when collecting independent reader evidence.
Treat source bytes, native-only records and inherited record spans as evidence, not portable design meaning.
Obtain independent source inventories and native acceptance before qualifying a route.
Do not copy retained evidence into another format or use it as an unrelated writer template.
