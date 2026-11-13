# Merge-queue cache scope

A cache saved by one merge-group run might appear to be available to the next candidate.
Each candidate runs on its own `gh-readonly-queue/main/...` ref.
A run can restore caches from its own ref and the default branch only.
The heavy queue jobs do not run again on the `main` push, so `main` never saves that cache.

Carry data between candidates in a workflow artifact.
Find the artifact through the repository artifacts API.
Accept only artifacts from same-repository runs on `gh-readonly-queue/` refs.
See [the sharded test suite](../../Changes/ShardedTestSuite.md) and [cache access restrictions](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching#restrictions-for-accessing-a-cache).
