# Uninitialized Fusion reflection values can contain persisted fields

## Expectation

An uninitialized member set with no reflected members might indicate an empty value or require an opaque payload fallback.

## Actual behavior

`ProgenitorAuxDataValueMetaType`, GUID `BE7E2847-FBC4-4898-A6E7-632A559A7F89`, remained uninitialized in the captured version-zero reflection catalog. Saved documents nevertheless store four bytes for each of its values. Kit reads them as one 32-bit field named `tag`. The name and the unsigned type come from earlier binary inspection and are not confirmed by a black-box experiment.

This affected 38 named metadata values in the corpus: 36 sweep-face progenitor records and two entity progenitor records.

## Workaround and evidence

Do not treat an uninitialized schema as an empty schema. Decode the saved records and check that every byte is consumed. [The value layout notes](../../../../re/Fusion/Reconstruction/EntityGraph/ProgenitorValues.md) describe the field; [the corpus summary](../../../../re/Fusion/Reconstruction/CorpusSemantics/Summary.json) records complete subsequent consumption.
