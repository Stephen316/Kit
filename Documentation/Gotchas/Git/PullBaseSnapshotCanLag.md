# Pull request base metadata can lag the branch ref

## Expectation

A pull request's `base.sha` could appear to identify the current target branch commit.

## Observed behavior

During PR #94 work on 2026-11-15, the REST pull response still returned base `1087ffe828caf3ef32b31f242ed3ebd69de30821`.
The target's `git/ref/heads/main` response already returned `d85e42479bccc79bea5e0c7eeca6a0411cc9e2a9`.
The pull response's synthetic merge `1fd73f04bde4aaf2b096a00f144f287d987f9bf5` had the newer base and head `b86f30c7e41abdc3812ada795a193377f6ddd220` as parents.
The response also reported `mergeable: true` and `mergeable_state: behind`.

These observations show different revision identities in one verification window.
They do not establish the internal cache cause or a general refresh interval.

## Workaround

Read the target branch ref independently and inspect the synthetic merge's parents.
Bind CI evidence to its actual checkout and candidate parents.
Invalidate merge-dependent evidence when the target moves.
Do not infer a current base from the pull response alone.
Do not treat a successful PR check as merge-group acceptance.
