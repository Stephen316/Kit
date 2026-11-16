# Read the automatic-scope Cut through the resolved footer

Run the [pinned automatic-scope archive command](ProvisionalScopeArchive.md) with `--compare-repeat` and `--inspect-map`. The continuous archive walk now reads the saved result choosers, body partition, through-all extent and footer in both exact provisional saves. It starts with the [previously resolved Cut scope bodies](AutomaticScopeTypedCut.md).

| Record | Byte positions | Checked result |
| --- | --- | --- |
| Body A chooser | 24,218–24,638 | Allocates object 459 for body 101 and feature 32. Its two faces allocate objects 460 and 471. |
| Body B chooser | 24,638–25,102 | Allocates object 483 for body 102 and feature 40. Its two faces allocate objects 484 and 495. |
| Chooser returns | 25,102–25,118 | Both saved owner references resolve to Cut object 430 around the empty secondary array. |
| Partition | 25,118–25,206 | Allocates marker object 507 at 25,132. The array at 25,154 stores atom/body pairs `(103, 101)` and `(104, 102)`, in the scope array's order. |
| Extent | 25,216–25,358 | Allocates `moEndSpec_c` object 508. The conditions are `(1, 0)`, with a null depth selector at 25,242. The start selects the sketch plane and allocates `moFromEndSpec_c` object 509. |
| Resolved-list footer | 25,358–25,362 | The zero footer consumes the remaining stream bytes. The next allocation index is 510. |

Each first chooser face retains the earlier Boss's first cap and four ordered sides. Each second face retains both earlier caps and Cut side occurrences 5, 6 and 8. Prior surfaces match the reached Boss by file, feature and saved clock. The two bodies have the same Cut-side identities within each save. Their bounding centres match the earlier Boss choosers. Body B uses the extended surface classes for its earlier Boss identities as well as for Cut-side records.

The repeat comparison checks these allocations, owner and occurrence order, partition pairs, extent and footer. Each report retains its own surface clocks and the five raw start-tail words. The fifth of those words also varies between saves and remains unclassified. Its value and the raw surface clocks are excluded from structural equality.

The exact paired typed report has SHA-256 `dabc53e8fde298b1d3752f06436f1cd5a1115dee64df1fef9f6edeebf7e1d76b`. The default repeat and single-archive reports reproduce SHA-256 `84d8a91c3f7fab14f870301c82621647c68f1110efe1070f929780df999fbace` and `4da047efcf25cb09ce91132549ef7c4d082bb851cf97edf1271cd9f4833079ac` respectively.

The replay verifies the saved two-body identities and depthless through-all extent in both provisional automatic archives. The [active-partition replay](AutomaticScopePartitionGeometry.md) independently measures both saved solids and their through-openings. The [bounded profile packet](AutomaticScopeSupportSheet.md) also resolves to the first Boss's support sheet. The persisted Auto-select policy and cross-format qualification still require the independent native automatic, explicit A and explicit A+B controls. [Native scope control](ThroughAllScopeControl.md)
