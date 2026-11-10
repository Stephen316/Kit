<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Transient CI artifact publication errors

The CI aggregate can finish every component check and upload its evidence, then
fail when GitHub's artifact metadata endpoint briefly returns 404 for the newly
published artifact. A successful upload alone does not establish that subsequent
evidence verification passed.

In [PR #53, attempt 1](https://github.com/TryUniCAD/Kit/actions/runs/42744787892/attempts/1),
the upload completed at 02:50:43 UTC on November 10, 2026, but the immediate request
for artifact `13731316590` returned 404. A later metadata request returned that
same artifact, unexpired, with its SHA-256 digest and workflow run
`42744787892`, bound to head `10902787d9b3c0879e1d5fd16303ae0d8d4fdd79`.
[Attempt 2](https://github.com/TryUniCAD/Kit/actions/runs/42744787892/attempts/2)
then passed without a source change.

For this evidenced transient failure, verify the exact artifact ID and owning
run, then rerun the failed workflow once. A repeated failure needs investigation;
do not skip artifact verification or relax its digest, revision, and provenance
checks. This observation does not establish a general consistency guarantee or
explain every artifact 404.

The race recurred in [PR #67, attempt 1](https://github.com/TryUniCAD/Kit/actions/runs/42903472751/attempts/1)
for metadata of artifact `13804166793`, then in [attempt 2](https://github.com/TryUniCAD/Kit/actions/runs/42903472751/attempts/2)
for downloading artifact `13804172032`. Both artifacts became readable after
the immediate verification failed. The upload-to-download boundary therefore
needs bounded retries rather than repeated workflow reruns.

The evidence verification step now allows four retries through
[`actions/github-script`](https://github.com/actions/github-script#retries),
including 404 responses. Authentication and validation failures remain exempt
from retries. Permanent API failures still fail the step after the retry limit;
digest, size, expiry, revision, and provenance verification remain unchanged.
Only the immediate post-upload verification client gets this retry policy.

Verification used remote workflow logs and subsequent reads of the exact
artifact IDs. No local tests ran. This workflow executes from trusted base code,
so the retry setting takes effect after the repair PR merges. See the
[gotchas log](../Gotchas/README.md) and [merge queue operations](../../MergeQueue.md).
