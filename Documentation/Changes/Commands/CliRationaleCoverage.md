# Align CLI declarations with the current rationale policy

The CLI and its process compatibility cases now include purpose comments above
declarations, module bindings, and inline lambdas, as required by current main.
Each comment explains the boundary or invariant being maintained. The comment
update changes no command, decoding, conversion, SDK, or process behavior.

The earlier CLI branch followed the previous no-comments policy. Main subsequently
enabled whole-tree rationale enforcement; the static checker reported 148 missing
comments in the combined branch. The user explicitly selected the new repository
rationale rule for this PR. See [the branch-policy gotcha](../../Gotchas/Ci/Commands/CliBranchesNeedRationales.md).

Verification uses the static rationale checker, Black, steering, path policy, and
whitespace checks. Tests, test collection, and decoding remain remote only.
Exact-head CI and configured review evidence are recorded in PR #119.
