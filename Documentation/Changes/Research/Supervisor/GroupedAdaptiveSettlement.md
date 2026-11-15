# Group settlement and adaptive capacity

The supervisor uses the controller's group finish response to decide whether a physical group can affect adaptive capacity.
A group with only stale member responses is excluded.
If the controller accepts at least one member's settlement, the group can still contribute one adaptive observation.
Group memory learning requires every member to complete and have its result accepted by the controller.
The supervisor retains the stop reason and controller response for each member in its event output.

This behavior applies to existing group protocol 1 runners and uses the existing supervisor configuration.

## Verification

The new grouped process case stops a worker for exceeding its sampled memory limit.
It rebinds the group's shared input immediately before the controller processes the original group's finish.
It checks that all three responses are stale, the original session emits no adaptive backoff, and jobs complete on the new generation.
The existing grouped memory and deadline cases cover accepted stop accounting.
Hosted Linux and macOS verification of the new case is pending.

See [the supervisor guide](../../../Reference/Research/ResearchSupervisor.md#optional-grouped-sessions) and [the stale-member gotcha](../../../Gotchas/Research/Supervisor/GroupedAdaptiveStaleMembers.md).
