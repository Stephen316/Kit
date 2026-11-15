# Retained semantic markers survive source relabeling

Interchange writes reject unresolved SOLIDWORKS equation and inch-dimension evidence even when the document source format is changed to `interchange.json` or another format. The checks walk root and embedded component documents and inspect the retained metadata and parameter attributes directly. Changing provenance does not establish the missing semantics.

Registry writes and direct JSON, Fusion, CATIA and FreeCAD methods use the same guards. The checks run before destination mutation and remain active with structural validation disabled. Native reading and explicit inspection serialization remain available.

## Verification and limits

The [review finding](https://github.com/TryUniCAD/Kit/pull/94#discussion_r4576681680) identified that equation and inch guards filtered on `source.format_id` while the support guard retained native-evidence checks. Source inspection confirmed that replacing the source format left unresolved markers intact but bypassed those filters.

Process integration cases read native input, persist and reopen relabeled neutral files, and exercise root and nested documents across seven direct writer spellings. Existing destinations and binary/text streams must remain unchanged; missing output directories must stay absent. Public API cases retain missing equation-reference and target checks after relabeling. A separate actual P04 inch input retains unresolved evidence through JSON persistence and must refuse both write and convert operations.

Steering, formatting and static typing are permitted local checks. No tests or native decoding ran locally. Exact-head remote verification remains required. This change resolves a refusal bypass; it does not qualify a source equation, a unit mapping or conversion.

See [the marker gotcha](../../Gotchas/Conversion/RelabeledSemanticMarkers.md) and [the reader guide](../../Reference/Research/SolidworksResearchReader.md).
