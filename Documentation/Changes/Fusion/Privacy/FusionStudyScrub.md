# Scrubbed account residue from the saved Fusion study corpus

## Behavior

The saved archives under `re/Fusion/Study/` were already on `main`.
Their protein material stores carried the same kind of account residue as the [branch fixtures](FusionFixtureScrub.md).
The residue was a hashed hub id, a user id, session ids and space collection ids.
Several of those values are identical to values that this branch had already replaced in its own fixtures.

[`ScrubSaved.py`](../../../../re/Fusion/LocalOracle/ScrubSaved.py) ran over the study archives together with the archives that this branch added.
It changed 117 study archives.
It also changed 3 branch archives, whose residue held key-less fragments of session and collection ids that appear with their keys only in study archives.
The [scrub ledger](../../../../re/Fusion/LocalOracle/ScrubLedger.json) records each archive's saved digest, committed digest and per-rule counts.

Study reports, censuses, frozen evidence digests and scripts that cited an archive digest or size now cite the committed one.
Reports that cite those reports by digest were updated in the same way.

Compressed evidence cites archive and member digests too.
Each `.xz` and `.tar.xz` file that held one was decompressed, updated and recompressed.
The recompression used the check type and preset that reproduce the original stream byte for byte.
Tar members keep their order and metadata.
The Mesh test source bundle and fifteen research evidence files changed this way.
Six of them also held the digest that a reflection file had before the [fixture scrub](FusionFixtureScrub.md).
Indexes and summaries that cite those files by digest or compressed size now cite the new ones.

Three third-party example bundles hold residue that the scrubber would also replace, but they do not hold this account's data and stay unchanged.

## Verification

`ReadDocument` models and `EmitParsed` round trips stayed equal for all 120 changed archives.
`ReadFusionDoc` documents for 119 of them differed only in the whole-archive digest and passthrough payload; the remaining archive raised the same error before and after.
Every changed byte lies in the unused capacity of a material store block.
A second run over all 292 ledger archives changed no byte.
No saved, superseded or member digest of a changed archive remains in a tracked file, including inside `.xz` streams and tar members.
Each recompressed stream has the original stream header and uncompressed length, and its content differs only in mapped digests.

Static checks ran locally; no local automated tests were run.
