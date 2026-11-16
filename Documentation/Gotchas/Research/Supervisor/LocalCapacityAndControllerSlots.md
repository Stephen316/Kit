# Local capacity and controller slots

## Expectation

A pool with CPU and memory headroom appears ready to start another job.

## Actual behavior

The controller also enforces one logical running-job limit shared across its pools.
A grouped worker can hold several logical slots while using one local worker slot.
A pool with local headroom can therefore receive a `concurrency limit` response from A03.

## Workaround

Use the observed controller refusal to explain the latest deferred claim.
Read local capacity separately to diagnose CPU, memory and adaptive limits.
When a current sample is visible, use its available logical jobs as a shared upper bound on additional physical sessions. Each member of a proposed group needs one free logical slot.
The next controller transaction decides whether a logical slot is available.

See [controller refusal evidence](../../../Changes/Research/Supervisor/ControllerCapacityRefusal.md) and [numeric controller capacity](../../../Changes/Research/Supervisor/ControllerCapacitySnapshot.md).
