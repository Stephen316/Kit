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

[Run 43663022455](https://github.com/TryUniCAD/Kit/actions/runs/43663022455/job/132656265358) retained the first complete report for PR head `480d9d3a7309490038519ad8735c2a55abd1e422`.
The 230,719-byte report has SHA-256 `bb1169ae1d7278535d63650f932f8071ae4976c069076a5a298cf40db046b7d0`.
Its 714 outcomes match the prior aggregate totals: 12 strict, 685 partial and 17 rejected.
The original baseline was committed unchanged as `re/automation/FusionOutcomes.json` at `b86f30c7`.
Its observed SDK checkout is `ec41e96ee4eb884e1097311a2a25cd6a1119cdec`.
GitHub records that checkout as the merge of base `1087ffe828caf3ef32b31f242ed3ebd69de30821` and the stated PR head.
Read actual candidate parents when verifying later runs: [pull base metadata can lag](../../Gotchas/Git/PullBaseSnapshotCanLag.md).
The SDK source digest verified at PR head `480d9d3a` is: `2884b881f89fff12e64391a3da3b2d0bf676904fa2df08481959dba617d00d63`.

The corpus process check now compares each later report with this committed baseline.
Its mutation scenarios also reject missing inputs, improved outcomes, duplicate records and mismatched corpus identities.
[The enforcement run](https://github.com/TryUniCAD/Kit/actions/runs/43663892794/job/132658933617) passed all five reader process scenarios at `b86f30c7`.
The complete 714-file outcome roster matched the unchanged baseline.
This completes A05b's outcome gate without closing A05c semantic qualification.
No local tests, decoding, or native application runs verified this change.

Outcome equality does not compare geometry, constraints, dependencies, or serialized document content.
Semantic qualification remains unverified. Portable completeness remains false. Native acceptance remains not established.
See [the reader guide](../../Reference/Research/FusionResearchReader.md) and [the evidence limitation](../../Gotchas/Research/FusionAggregateCensus.md).

### Circle-reader baseline refresh

[The hosted Fusion reader job](https://github.com/TryUniCAD/Kit/actions/runs/43927281416/job/133510198551) on PR head `1c723c6beaded87d9309a7d369dd7a6749ab74ea` failed the outcome equality assertion and published [the complete census](https://github.com/TryUniCAD/Kit/actions/runs/43927281416/artifacts/14256264175) before the workflow was canceled.
The 230,598-byte report has SHA-256 `e09ed70f274b1c3decb3d3cedf065e94c51b7ee9b0ff2570ac5e38217e443805`.
Its tested merge commit `9af5672130f74d1c507e0e1d1a76455fff4624f0` has base `1d294381340a36ce8e4d9e288e73d995da12fcd7` and the stated PR head as its two parents, and its tree matches that head.

All 714 path, Git blob and SHA-256 pins, all four reader-tool hashes and the aggregate digest of 3,391 Python source files match the Git objects.
The four measured diameter and radius controls moved from partial to strict.
The separate legacy `sketches-0ccea2ac0f9c/radius.f3d` input remained partial, with strict refusal changing from an unknown native class to an unmodeled native semantic class.
The other 709 outcomes are unchanged.
The refreshed baseline retains the complete observed report byte for byte, with 16 strict, 681 partial and 17 rejected outcomes.
Earlier runs retain their original results. This refresh records reader outcomes only.
The [licensed radial readback](Readers/FusionCircle/FusionStrictRadialPrototype.md) has its own application evidence and authoring limits.
