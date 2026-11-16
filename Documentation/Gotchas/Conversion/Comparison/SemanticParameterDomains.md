# Parameter validation does not establish primitive value domains

## Expectation

A validated portable document contains parameter magnitudes that match each `ParameterValue.kind`.

## Observed behavior

`ParameterValue` accepts a shared `str | int | float | bool` value union alongside a separate kind.
The document validator checks identities, references and feature contracts without enforcing every primitive kind/value pairing.
The earlier comparator could therefore observe the same malformed number, integer, boolean or string on both sides and report graph equality.
Python's Boolean subtype relationship also makes a general integer check insufficient.

## Workaround

The [semantic value-domain check](../../../Changes/Research/Readers/Comparison/SemanticValueDomains.md) records malformed primitive values and unknown kinds as unresolved evidence before equality can succeed.
It retains the observed kind, value, unit and evidence digest.
The shared model and codec remain unchanged; valid dimensional parameters retain their existing quantity policy.
Public command process coverage supplies sealed malformed and valid documents on both sides.
No local tests were run; hosted verification and native semantic qualification remain separate requirements.
