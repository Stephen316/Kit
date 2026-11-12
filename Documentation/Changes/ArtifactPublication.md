<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Transient CI artifact publication errors

## Problem

The aggregate can upload evidence successfully and then fail to read the new artifact.
A successful upload does not prove that later verification passed.

## Recorded incidents

| Incident                                                                                  | Observed evidence                                                                                                                                  |
| ----------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| [PR #53, attempt 1](https://github.com/TryUniCAD/Kit/actions/runs/42744787892/attempts/1) | Upload completed at 02:50:43 UTC on 2026-11-10. Immediate metadata access returned 404 for artifact `13731316590`.                                 |
| Later PR #53 read                                                                         | The same unexpired artifact became readable with its digest and owning run `42744787892`. Its head was `10902787d9b3c0879e1d5fd16303ae0d8d4fdd79`. |
| [PR #53, attempt 2](https://github.com/TryUniCAD/Kit/actions/runs/42744787892/attempts/2) | The run passed without a source change.                                                                                                            |
| [PR #67, attempt 1](https://github.com/TryUniCAD/Kit/actions/runs/42903472751/attempts/1) | Immediate metadata access failed for artifact `13804166793`.                                                                                       |
| [PR #67, attempt 2](https://github.com/TryUniCAD/Kit/actions/runs/42903472751/attempts/2) | Immediate ZIP download failed for artifact `13804172032`.                                                                                          |

Both recorded PR #67 artifacts became readable after the immediate failure.
These observations do not explain every artifact 404.
They do not establish a general consistency guarantee.

## Repair

The immediate verification client permits four retries through [actions/github-script](https://github.com/actions/github-script#retries).
The retry policy includes 404 responses.
Authentication and validation failures remain exempt from retries.
Permanent API failures still fail after the retry limit.
Digest, size, expiry, revision, and provenance checks remain enabled.
Only the immediate post-upload verification client uses this policy.

## Recovery

1. Identify the exact artifact and owning run.
2. Confirm evidence of a transient publication failure.
3. Rerun the failed workflow once when justified.
4. Investigate recurrence before another retry.

Do not skip artifact verification to obtain a passing status.

## Recorded verification

The original investigation used remote logs and subsequent reads of the exact artifact identifiers.
No local tests ran.
The reporter uses trusted base code, so feature-branch changes take effect after merge.
See [the gotchas log](../Gotchas/README.md) and [queue operations](../../MergeQueue.md).
