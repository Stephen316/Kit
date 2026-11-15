# Exact Fusion reader outcome census

A05b adds `re/automation/FusionCensus.py` to retain and compare the complete pinned Fusion reader outcome roster.
The collector reads existing reader summaries and receipts. It does not decode CAD files.

## Collection

Use a complete set of summary shards from one reader run and the exact corpus manifest.
Select an unused output file. Its parent directory must exist.

```shell
python re/automation/FusionCensus.py collect --manifest re/automation/Corpus.json --summary /tmp/reader-a/summary.json --summary /tmp/reader-b/summary.json --output /tmp/FusionReaderCensus.json
```

The collector requires every pinned F3D/F3Z path exactly once.
It binds each outcome to the input SHA-256 and Git blob.
All shards must share the corpus, manifest, SDK source, tool, runtime, and reader-option identities.
Decoded receipts must match their summaries and pinned inputs.
Strict and partial results retain separate modes. Partial results retain the strict rejection reason.
Rejected files retain their reason. Reader errors also retain their exception type.

The corpus process check writes this report before its temporary reader output is removed.
Set `KIT_FUSION_CENSUS` to an unused report path to retain it for remote artifact publication.
Without that variable, the check uses its temporary directory.

## Comparison

Review the complete remote report before committing it as an expected baseline.
Preserve the report's observed SDK revision and source fingerprints.

```shell
python re/automation/FusionCensus.py check --expected re/automation/FusionOutcomes.json --actual /tmp/FusionReaderCensus.json
```

The comparison requires the same corpus revision and manifest digest.
It rejects changed input identities, missing or additional paths, modes, rejection reasons, and error types.
Improvements require review before baseline replacement, as regressions do.
The baseline and actual SDK identities remain separate because later revisions can preserve the same reader outcomes.

Exit `0` means collection succeeded or the outcome roster matched.
Exit `3` means the roster changed. Exit `1` means an input or publication error.
Inputs are bounded to 32 MiB and rosters to 1000 paths.

## Evidence and limits

The [prior remote job](https://github.com/TryUniCAD/Kit/actions/runs/43656612973/job/132636421153) reported 714 assets at `c1c3fcce5b8b67373113ec44ad5d122a52bd7260`.
Its aggregate totals were 12 strict, 685 partial, and 17 rejected outcomes.
That run retained no per-file Fusion report. Those totals cannot establish an exact baseline.

This change adds report emission and checker process coverage using the real corpus results.
The new remote report, reviewed baseline, and enforced baseline comparison remain required before A05b can complete.
No local tests, decoding, or native application runs verified this change.

Outcome equality does not compare geometry, constraints, dependencies, or serialized document content.
Semantic qualification remains unverified. Portable completeness remains false. Native acceptance remains not established.
See [the reader guide](../../Reference/Research/FusionResearchReader.md) and [the evidence limitation](../../Gotchas/Research/FusionAggregateCensus.md).
