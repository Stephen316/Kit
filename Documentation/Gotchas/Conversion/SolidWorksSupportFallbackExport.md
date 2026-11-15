# A decoded fallback plane is not a qualified sketch support

## Expectation

A structurally valid sketch with a valid `support_plane_id` can appear safe to export.

## Observed behavior

`Native.SupportPlaneRef` can return a framed fallback when no explicit sketch support reference is resolved.
`Adapter.SketchA` preserves that plane identifier and the `stream-order` or `unresolved` source classification in the neutral sketch.
The actual support can differ from the fallback. The saved 2026 YZ parts exposed this discrepancy in research evidence.
The [review finding](https://github.com/TryUniCAD/Kit/pull/94#discussion_r4576597583) identified that ordinary public reads did not receive the research-reader marker.
The marker-only write gate therefore did not reject these ordinary native-derived documents.
Interchange serialization also preserves this fallback evidence, so changing file format does not resolve the support association.

## Workaround

Keep inspection available and reject output with unresolved support evidence at the common write guard.
Require the existing explicit-reference classification and no unframed identifier for SOLIDWORKS-derived sketches.
Inspect source attribution, provenance, and retained native support attributes in nested documents too.
Do not promote a coincidentally correct stream-order fallback to an explicit reference.
Complete the native support-reference and class-ownership investigation before implementing an additional production mapping.
The [write-gate change](../../Changes/Research/SolidWorksSupportWriteGate.md) records the refusal and verification scope.
