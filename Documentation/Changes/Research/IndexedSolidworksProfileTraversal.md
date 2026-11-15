# Indexed SOLIDWORKS profile traversal

## Behavior

A04c profile discovery now builds marker-position and vertex-edge indexes once for each candidate edge collection.
Rectangle-header ownership looks up the first owned edge through the marker-position index.
Connected-component traversal visits each connected vertex and its incident edges instead of repeatedly scanning every remaining edge.
Both rectangle and six-edge polyline discovery use the indexed traversal.

The change retains existing marker eligibility, coordinate checks, edge ordering, header validation, and source offsets.
It does not change the native grammar or establish new semantic qualification.
No public command or configuration option changes.

## Verification

Source inspection identified a marker-list scan for every rectangle and repeated remaining-edge scans for disconnected components.
The new native-file integration cases append independently encoded marker records to an existing research fixture and rebuild its container.
They exercise one and 64 disconnected rectangles, with and without headers, alongside a six-edge polyline.
Assertions cover decoded coordinates, rectangle count, header ownership, and the exact retained marker offsets.
These parser fixtures are not vendor-accepted CAD output.

No local tests, decoding runs, test collection, CAD applications, or model calls ran.
Pinned Black formatting passed for the five focused files; the changed native traversal was formatted without retaining unrelated baseline formatting edits.
Pyright reported zero errors for all six changed Python files, and mypy reported no issues for those files.
Focused steering compliance passed for five files; the complete tracked-tree path policy and staged whitespace checks passed.
Pyright also reported three unsupported settings already present in the repository configuration.
Runtime regression results remain a separate remote CI boundary.
No native conversion or application acceptance is claimed.

See [the repeated-scan gotcha](../../Gotchas/Conversion/SolidworksProfileTraversal.md), [the formatter exclusion gotcha](../../Gotchas/Ci/Policy/BlackResearchExclusion.md), and [the reader guide](../../Reference/Research/SolidworksResearchReader.md).
