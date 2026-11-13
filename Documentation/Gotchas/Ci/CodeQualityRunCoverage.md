# Code Quality run coverage

The managed Code Quality jobs might appear on every PR with the same language list.
GitHub does not run Code Quality for fork PRs.
[PR #94](https://github.com/TryUniCAD/Kit/pull/94) has no Code Quality run, and its aggregate stayed pending.
GitHub also adds or removes analyzed languages when the repository languages change.
Do not require fixed `Analyze (<language>)` names.
Match the job pattern, and expect a run only for same-repository PRs that change analyzed source.
See [the repair](../../Changes/CodeQualityApplicability.md) and [the default setup scope](https://docs.github.com/en/code-security/concepts/code-scanning/setup-types).
