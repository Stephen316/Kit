# FreeCAD process helpers stay outside test discovery

The initial-shape and attestation process modules now name their internal helpers `ReadCachedBody` and `AssertTargets`.
Kit's `python_functions` configuration collects `Check*` functions, including undecorated helpers with arguments.
The previous helper names therefore became two unintended test entries and requested nonexistent fixtures.
The rename preserves every process case, helper call and assertion; discovery rules and CI gates remain unchanged.

At exact source `161885d8ec4442ddc2558a740fd2cd153a6c0819`, the source owner reported 477 hosted archive passes and two setup errors from those helpers.
All 54 intended new cache and attestation cases passed within that run.
The setup errors still made the stage unsuccessful; this is not full-suite or current-head acceptance.
[Source-bound hosted finding](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6931236006)

Verification of this repair is static only; no local tests or collection ran.
Hosted discovery and execution must confirm the two helpers are absent while all intended cases remain.
The [discovery gotcha](../../Gotchas/Ci/Testing/CheckPrefixCollectsHelpers.md) records the naming boundary.
Native acceptance and broader route qualification remain separate.
