# Licensed SOLIDWORKS through-all scope evidence

The three-case campaign completed on SOLIDWORKS `34.4.1.1011` at source revision `e3d1d66e9e65f0b9366586865c7d0776970db057`. An independent process reopened each saved part read-only and rebuilt it. The watchdog observed both process exits and confirmed the private job drained. The [evidence comparator](CutScopeReadback.md) accepted the native report, archive hashes, source pins, and independently measured geometry.

| Scope | Native selected bodies | Measured affected bodies | A volume (mm³) | B volume (mm³) | Saved archive SHA-256 |
| --- | --- | --- | ---: | ---: | --- |
| All bodies | Empty, Feature Scope false | A and B | 7200 | 600 | `3e3bad3a13458be81da35dd41751edbccf1975269addf7db49ae19efcdc7a6df` |
| Explicit A | A, Feature Scope true | A | 7200 | 1000 | `943873393637f8aaf6c6a3d98a0f84bac8b9dceab07ef2b943b652319cfe3970` |
| Explicit A+B | A and B, Feature Scope true | A and B | 7200 | 600 | `5476c33f5d1210e0ee789322147bf8b3fbe7c26d17ff54c5751a8dcd1796a04d` |

The report independently observed these values before save, after reopen, and after rebuild within the recipe tolerances. All bodies and Explicit A+B agreed on every compared body field at each stage and retained their distinct scope policies. Body B remained at 1000 mm³ for Explicit A and differed from Explicit A+B in volume and face, edge, and vertex counts.

Direct `FeatureCut4` created the All bodies case. The direct explicit calls returned null after checking the selections. The isolated retry assigned `DispatchWrapper[]` body references to the editable feature definition and verified the requested roster before `ModifyDefinition`. Both explicit saves retained their scope and cleared Auto-select. [Explicit Cut retry](ScopeExplicitFallback.md)

| Retained evidence | SHA-256 |
| --- | --- |
| Fixed specification | `298cf204b0e4329186b35d9cc46e36525e3ef2119dc7ddb870e73a5f86289d52` |
| Native report | `2c61ac4921556b0d3d36c12a7987e25b7d40fa9cab0f631a23b9d7b241d36444` |
| Watchdog receipt | `2069d023ad89c515ccea253a6d088fde85bffc8d115faf80454f46a47696181b` |
| Normalized comparator result | `4819b725a3ea7094eb8a31267df02ca1ff710edaa6f94cbe828a687ca8aea5d2` |

The licensed Fusion campaign and paired scope comparison remain open. This two-body discovery scope uses its own specification and leaves the frozen P05 holdout reserved.
