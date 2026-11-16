# Native reader artifact worker

The research `reader.neutral` job reads one pinned native Fusion F3D or SOLIDWORKS part through `convert.api.ApiOpen.OpenDocument`.
The worker uses the existing version 1 single-job session, content-addressed input descriptors and controller output-artifact contract.
It checks the normalized definition, input binding and full controller snapshot fingerprint before reading the source.
The raw source SHA-256 is verified against both the input descriptor and the decoded document's source identity.

The job consumes exactly one input role, `source`, and requires exactly these options:

```json
{
  "scope": "current-p01-observation",
  "source_format": "fusion.f3d",
  "strict": false,
  "configuration": null
}
```

`source_format` is `fusion.f3d` or `solidworks.sldprt`.
`strict` is an explicit boolean; the worker never retries with different strictness.
`configuration` is null or printable text of 1–256 characters.
The underlying reader still applies its format-specific configuration rules.
The partial Fusion reader uses a positive decimal history identifier when a configuration is supplied.
The strict Fusion reader has a different native coverage contract and may refuse captured controls.
The SOLIDWORKS strict B-rep path refuses missing or unreadable Parasolid payloads.
Use an explicitly declared partial observation when that is the intended research task.

Register the kind using the actual supported Python executable, the path to `re/automation/NeutralReaderRunner.py`, and the literal `{session}` argument.
Generate its compact records schema with `python re/automation/NeutralReaderRunner.py --schema` and point the existing runner registry's `result_schema` at that file.
The existing controller accepts the new kind without a dispatch edit.
The adapter must support version 1 output artifacts.

## Retained artifacts and qualification

The raw input limit is 256 MiB.
The worker always requests B-rep and tessellation and preserves the public reader's full document, metadata, native payloads and diagnostics.
It does not remove fields to improve comparator status.
SOLIDWORKS containers with `Kit/Interchange` are refused before the public read, because embedded neutral documents do not supply independent native evidence.
Fusion reads follow the native parser; this worker does not create or consume a neutral carrier as substitute evidence.

The worker validates the actual document, serializes it through the existing typed codec, reconstructs it, validates it again and requires exact deterministic reconstruction.
It publishes two artifacts, each limited to 32 MiB and written incrementally through a private temporary file:

- `neutral-document`, at `neutral-document.json` relative to the session work directory, contains the complete codec document
- `reader-evidence`, at `reader-evidence.json`, contains the independent `ReaderEvidence.reader_evidence` inventory, unresolved records, source seal and exact definition/fingerprint/read options

The small `result.json` records receipt retains source, document and evidence hashes and sizes, the controller fingerprint, definition seal, supplied rule/tool version labels and explicit read options.
It also records a SHA-256 over the sorted actual SDK Python source inventory and individual hashes of the worker and its direct research helpers.
The worker checks this implementation identity before decoding and again before publishing its receipt; changed source refuses the attempt.
Source inventory is bounded to 100,000 SDK Python files and 512 MiB of hashed source bytes.
These observed source hashes do not turn supplied version labels into verified Git revisions.
The existing artifact intake retains the full outputs after session cleanup.
An oversized artifact or failed read refuses the process before a successful result receipt.
No partial document is returned as completed output.

Controller outcome `completed` means the observation and its artifact custody finished.
Every receipt and evidence artifact retains `semantic_qualification: unverified`, `native_acceptance: not_established` and `portable_complete: false`.
Full native evidence remains unresolved when a downstream `semantic.compare` job consumes a `neutral-document` dependency artifact.
Equal observed values cannot establish independent native interpretation or any CAD acceptance criterion.

## Verification evidence

Static formatting, syntax and whitespace checks were performed; no local tests, collection, reader commands or native application runs were executed.
The dedicated Archives process coverage uses the current checkout's tracked raw P01 Fusion and SOLIDWORKS capture files, with explicitly chosen `strict: false`.
It invokes the real registry schema, controller, supervisor and both worker processes.
It checks source/fingerprint seals, retained metadata and unresolved evidence, durable artifact selectors into semantic comparison and cleanup.
Independent worker subprocess cases refuse changed source bytes, changed fingerprints, missing pins and an independently authored embedded Kit container.
Hosted process execution remains required.

Stephen316 [reported a private Windows controller operation](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6927190826) at exact revision `7317092e37f52d6bfc3f26449e2b16a5bd82e86b`, now preserved in this PR's accepted ancestry.
Three strict P03 reader jobs and two dependent comparisons completed in 44.05 seconds, each on its first attempt, with zero stale jobs or orphans.
The operator reopened and hash-checked all five accepted result/receipt pairs and eight output artifacts through the controller.
Each comparison used the exact accepted SOLIDWORKS document and its assigned Fusion document, with full saved metadata and the unverified qualification fields retained.
The private summary SHA-256 is `eca1dcd25e36b3384e405576b750a25f7f9adfedd65c48de280709d0ab301cea`.
This source-bound operator observation does not replace current-head hosted checks, independent semantic qualification, native application acceptance or the two-week pilot.
P02 and P05 were outside the operation.
