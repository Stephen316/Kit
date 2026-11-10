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

This entry records an operational workaround, with no workflow or protection
changes. Verification used remote workflow logs, artifact metadata, and the
successful rerun. No local tests ran. See the [gotchas log](../Gotchas/README.md)
and [merge queue operations](../../MergeQueue.md).
