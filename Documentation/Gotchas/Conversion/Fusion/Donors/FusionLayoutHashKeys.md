# A table keyed by a layout hash does not scale

## Expectation

A Form cage converts to the same B-rep each time.
A table keyed by a hash of the cage layout can therefore store the stencils for each layout.

## Actual behavior

The Form writer kept eight per-layout stencil tables and eight shapes, keyed by a SHA-256 of the exact link table.
Some table rows were fitted to the probe cages.
The shapes copied the fit tolerances and labels of the Fusion carrier.
The key was not canonical.
The same box with other vertex numbers missed the table.
Any new layout had no entry, so the writer refused it.
Each new layout needed a new Fusion capture, so the method did not scale.

## Workaround

Derive each stencil from the local neighbourhood of its face in the cage.
Handle extraordinary points of any valence, boundaries, corners, creases and weights with rules, not entries.
Compute tolerances and labels.
Validate the rules on layouts that they were not fitted on.
Keep fitted tables only in `re/` as research evidence.
See the [donor data ban](../../../../Reference/Research/FusionDonorBan.md).
