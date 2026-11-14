# Generic-tag counts are primary byte lengths

## Expectation

Small leading integers in generic-tag groups can appear to identify body, face, or edge categories.
The next integer after primary text can appear related to history generation.

## Actual behavior

In all 441 generic-tag groups of the research corpus, the leading integer equals the byte length of the primary text.
Kit names the later fields secondary identity, operation identities and approach identity.
Those names come from earlier binary inspection and are not confirmed by a black-box experiment.

The earlier body writer emitted a fixed count of three.
That matches primary text `301` but disagrees with four-digit primary text such as `1701`.
Earlier feature callers supplied matching counts for their short labels, which concealed the mistaken selector interpretation.

The native cuboid body has secondary identity seven and primary text `301`.
That secondary identity matches its body progenitor tag, rather than naming the current history state.
The controlled cylinder uses secondary identity four.

## Workaround

Construct semantic `FeatureTag` values without a supplied length.
Derive the encoded count from the primary bytes and reject inconsistent counts when reading.
Use `BodyIdentity.SecondaryId` for the explicit secondary identity.
Keep history generation in `HistoryState`, where it has its own independent field.

The qualified primary-text domain is printable ASCII, with one through 255 bytes.
Kit keeps tag identities as signed 32-bit values even when the stream uses 64-bit integer tokens.
That width comes from earlier binary inspection and is not confirmed by a black-box experiment.

## Evidence

The [generic-tag report](../../../../re/Fusion/Reconstruction/CuboidHistory/GenericTagEvidence.json)
records 441 consistent groups from the research corpus.
The [semantic correction](../../../Changes/Fusion/FusionGenericTagSemantics.md)
describes API migration and archive integration coverage.

Previously accepted three-digit authoring defaults retain their serialized bytes.
The correction does not retrospectively establish native acceptance for earlier malformed four-digit output.
