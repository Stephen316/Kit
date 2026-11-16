# Initial open can expose geometry while marked Touched

An assertion intended for the state after rebuild cannot substitute for measuring initial geometry.
At exact source `161885d8ec4442ddc2558a740fd2cd153a6c0819`, the operator observed three generated rectangle features marked `Touched` immediately after opening in FreeCAD 1.1.4.
All three already exposed one valid editable solid with the expected bounds, volume and centroid before explicit recompute.
Recompute then changed their state to `Up-to-date`.
[Source-bound observation](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6931310116)

Record initial state and measured geometry separately.
Retain post-rebuild state checks and all geometry, edit, restoration, save and fresh-reopen requirements.
Do not treat `Touched` as proof of usable geometry or allow it to mask a failed solid, repair requirement or empty document.
The [witness entry](../../../Changes/FreeCad/FreeCadInitialOpenWitness.md) records the scoped controls and seals.
The earlier uncached zero-solid initial-open failure remains a failure at its original source.
