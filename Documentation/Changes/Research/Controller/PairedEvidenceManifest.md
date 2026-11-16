# Paired supplemental evidence preflight

## Purpose and scope

`re/automation/PairedEvidenceManifest.py` validates a sealed supplemental-evidence request before coordinated admission.
It preserves the original captures, receipts, measurements and family splits.
It does not replace `PairedCaptureIntake.py` or the privately retained Fusion intake implementation.
It never qualifies a pair or changes a reader's frozen rules.

The command replays the existing public SOLIDWORKS principal and circle verifiers against owner-local raw receipt chains.
A copied normalized report cannot substitute for those inputs.
The replay must reproduce the independently supplied normalized-report digest.
Its exact native roster must also match both the selected historical capture and target Git revisions.

The public adapters cover P01/P03 principal observations and P02 circle observations.
Fusion and original P04 supplemental verification require their existing owners' source handoffs.
The command records those dependencies and returns blocked readiness, including when the referenced commits exist without an integrated verifier contract.
P05 and its descendants remain outside this command.

## Before you start

Use Python 3.11 or later and Git in a complete checkout with the required source and capture commits.
Use the repository's pinned research environment when a public verifier needs the SDK.
The checkout's `HEAD` must equal the manifest's target revision.
Tracked source under `src/` and `re/automation/` must match that checkout.

Obtain the manifest SHA-256 from its independent owner before reading the file.
Obtain the input and normalized-report digests from the retained native run's independent record.
Keep private evidence outside the checkout in a dedicated directory.
Use absolute paths without symlinks or Windows reparse points, including their parent directories.

## Manifest contract

The JSON object has exactly these fields.
Duplicate keys and unknown fields are refused.

| Field                   | Required value                                                                 |
| ----------------------- | ------------------------------------------------------------------------------ |
| `version`               | Integer `1`                                                                    |
| `scope`                 | `paired_supplemental_preflight`                                                |
| `target_revision`       | Full lowercase Git commit SHA for the current checkout                         |
| `capture_revision`      | Full lowercase Git commit SHA retaining the original selected captures         |
| `frozen_rules_revision` | Full lowercase Git commit SHA reserved for subsequent frozen-rule adjudication |
| `specifications_sha256` | SHA-256 of `re/automation/PairSpecs.json` at the target revision               |
| `recipes`               | Sorted, unique selection from P01, P02, P03 and P04                            |
| `evidence`              | Exactly one SOLIDWORKS and one Fusion record for every selected recipe         |

Every evidence record contains `application`, `recipe` and the full native collector `source_revision`.
Fusion records and P04 records additionally contain only `handoff_revision`, a full source-only handoff commit SHA.
Their output identifies whether both source commits are locally available.
Availability alone does not establish the missing verifier contract.

The public SOLIDWORKS P01, P02 and P03 records instead require these fields.

| Field               | Required value                                                                                      |
| ------------------- | --------------------------------------------------------------------------------------------------- |
| `verifier_revision` | Full commit SHA containing the public verifier source                                               |
| `verifier_sha256`   | SHA-256 of that verifier's committed bytes, which must match the local source                       |
| `input_directory`   | Relative directory beneath the private evidence root, with no absolute path or parent traversal     |
| `input_sha256`      | Principal dispatch SHA-256, or P02 receipt SHA-256                                                  |
| `report_sha256`     | SHA-256 of the exact normalized JSON emitted by the public verifier, including its terminal newline |

P01/P03 use `PrincipalReadbackEvidence.report` and its documented dispatch, plan, measurements and receipt layout.
P02 uses `CircleReadbackEvidence.verify` and its documented plan, measurements and receipt layout.
Each source pin, native owner, control and original archive check remains in that existing verifier.
The preflight does not execute a manifest-selected program or import a supplied module.

## Procedure

1. Create and independently seal the manifest with the owning native operator.
2. Place each original receipt chain in its declared private directory.
3. Run the preflight with the independently supplied manifest digest.

```shell
python re/automation/PairedEvidenceManifest.py \
  --manifest /private/path/PairedEvidence.json \
  --manifest-sha256 MANIFEST_SHA256 \
  --evidence-root /private/path/NativeEvidence
```

Replace the example paths and digest before running the command.
The command reads evidence and writes its JSON report to standard output.
It does not write artifacts or change controller state.

## Expected result and failures

Every report retains `qualified_pairs: 0` and `qualification: not_evaluated`.
The requested frozen-rule revision is recorded without executing it or consuming holdout files.
A successfully replayed public lane reports `verified_same_format_observations`.
A missing private directory reports `waiting_private_evidence`.
Fusion and P04 lanes report `waiting_source_handoff` until their owning contracts are integrated.

| Exit | Meaning                                                                         | Required action                                                                       |
| ---- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| `1`  | Invalid manifest, changed pin, unsafe custody path, or refused raw-chain replay | Restore the independently pinned inputs or resolve the stated contract error          |
| `2`  | Dependency report produced, with readiness blocked                              | Supply the missing private evidence or source-only handoff through its existing owner |

There is no qualification-success exit.
The separate admission owner must adjudicate complementary evidence and frozen-reader outcomes.
Source existence, a digest match and a single-vendor replay do not establish paired qualification or native conversion support.

The manifest limit is 1 MiB.
Private receipt files are limited to 32 MiB each, with at most 64 entries and one nested directory level.
Pinned source and native archive reads retain the command's bounded Git-output limit.
Symlinks, reparse points, path escapes, duplicate application/recipe identities and oversized inputs are refused.

## Verification evidence

Source inspection at `adee447ebc3e8202f167d54d31af5adba4fe60d7` confirmed the two public verifier APIs and their normalized serialization.
The source-only Fusion handoff commits `9cc97c48621fe46d88916100e72259618182f3d6` and `27c0d9d0b995da4ac7a7704d26b3b5716c10ca6e` were unavailable locally.
GitHub's commit API returned 404 for both in the base and head repositories during this audit.
The [handoff owner](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6921995314) retains those source commits and private evidence locally.

The new hosted archive process cases invoke the real standalone command with committed Git source pins.
They cover blocked readiness, exact source/specification pins, dual-application identity, forbidden P05 selection, manifest seals, size limits and linked paths.
Both public verifier entry points must refuse a normalized JSON object presented as their raw receipt chain.
No local tests, collection, decoder experiments or native application runs were executed.
Positive replay of the private licensed reports and exact-head hosted results remain separate evidence requirements.

## Related information

- [Paired capture intake](../PairedCaptureIntake.md)
- [Original lineage audit](../PairedCaptureLineageAudit.md)
- [Principal readback contract](../Workers/SolidWorks/PrincipalReadback.md)
- [P02 circle contract](../Workers/SolidWorks/CircleBindingReadback.md)
- [Step register](../../../Reference/Research/AutomationSteps.md)
