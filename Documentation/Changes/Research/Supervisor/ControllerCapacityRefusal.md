# Controller capacity refusal evidence

When A03 refuses a claim because its logical running-job limit is full, the supervisor retains the transaction reason in `capacity.decision.controller_refusal`.
The entry identifies the `a03` adapter and its exact `concurrency limit` reason.
Both the direct controller invocation and the Windows warm claim helper preserve this observation.

The supervisor emits one `controller_claim_refused` event when a pool first observes this condition.
A later successful claim or empty queue clears the observation.
The existing snapshot owner and freshness checks apply to the status field.
Local CPU and memory capacity continue to describe the physical supervisor slots.
A03 still enforces the shared limit transactionally for all logical jobs, including grouped members.
A03 checks the shared limit before it searches for runnable jobs.

## Verification

The hosted process case holds the controller's only logical slot in one pool while a second pool still has local worker capacity.
It checks the actual refusal event and live status while the second job remains queued with zero attempts.
After a pause releases the held slot, the second job completes once and status clears the refusal.
Linux and macOS use the direct adapter and Windows uses the warm claim helper.
Exact-revision hosted verification remains pending.

See [supervisor commands](../../../Reference/Research/ResearchSupervisor.md#commands) and [controller slot reporting](../../../Gotchas/Research/Supervisor/LocalCapacityAndControllerSlots.md).
