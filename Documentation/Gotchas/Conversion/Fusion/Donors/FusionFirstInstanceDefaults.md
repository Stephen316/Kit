# First-instance feature defaults carry values from one control

## Expectation

A defaults table that takes the first value of each field from the feature controls gives safe fallbacks.
Each feature writer sets the fields that matter, so a fallback never reaches the output.

## Actual behavior

The feature vocabulary generator took the first instance of each field from 16 controls.
The table then held case values such as a `DRPoint` at (2, 1.5, 2).
It also held a pattern operation id map such as `{2: 309, 3: 307}`.
Other entries were a body operation type map `{301: 33}`, cached line segments, face pick points and an integer parameter of 3.
A feature path that left a field unset emitted the captured value without an error.
The output then pointed at operations and geometry from another document.

## Workaround

Build the defaults from the schema: zero, empty, false or identity for each type.
Keep a non-type default only when unrelated controls prove it constant, and record that proof.
Make every geometric and id field from the feature that Kit writes.
Fail when a feature leaves such a field unset.
See the [donor data ban](../../../../Reference/Research/FusionDonorBan.md).
