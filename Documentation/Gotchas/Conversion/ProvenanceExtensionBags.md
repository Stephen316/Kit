# Provenance can retain unclassified native fields

## Expectation

Source identities and provenance spans are evidence about where a portable record came from.
Renaming those identities should not determine semantic correspondence.

## Observed behavior

`CadSource.attributes` and `Provenance.attributes` also accept arbitrary extension values, including retained native bytes.
Removing the whole source or provenance record from comparison can therefore remove unresolved source content.
`Provenance.confidence` can separately record an uncertain interpretation.
These contracts are visible in [RecordSource.py](../../../src/interchange/Records/RecordSource.py) and [RecordProvenance.py](../../../src/interchange/Records/RecordProvenance.py).

## Workaround

Keep identity and span digests as observations.
Report nonempty source and provenance extension bags as unresolved until their semantics have independent evidence.
Report non-unit provenance confidence as unresolved.
The [portable comparator](../../Changes/Research/Readers/Comparison/SemanticGraphComparison.md) follows this rule; equal retained bytes do not establish portable semantics.

Source inspection established this contract during A06 implementation.
Hosted process coverage remains required; no native conversion acceptance is claimed.
