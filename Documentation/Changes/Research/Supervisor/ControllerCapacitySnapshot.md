# Shared controller capacity in supervisor status

With the built-in A03 adapter, an evaluated pool can show `capacity.decision.controller_capacity` in `supervisor status`.
The view includes `maximum_running_jobs`, `running_jobs`, `available_jobs`, `physical_sessions`, and `age_seconds`.
`effective_capacity` and `effective_active_limit` cap the local physical limits at the pool's existing physical sessions plus free logical slots.
`effective_additional_sessions` caps local room for another session at the number of free slots.

One group uses a physical worker and one logical slot per member.
The slot count covers all pools and can change after the sample, so use these figures as upper bounds for dispatch. A03 continues to decide each claim in its writing transaction.
The existing local decision and exact `controller_refusal` remain available independently.

The live supervisor samples the ledger through an owner-fenced read transaction at most once every five seconds. The status command reads the owner snapshot.
The sample can be omitted when a read is busy, ownership is uncertain, reconciliation is pending, a sampled lease or deadline has expired, or the supervisor has since started or removed a session.

The hosted process case holds three grouped leases and one singleton lease against four available controller slots. It checks a partially occupied controller, a full controller with positive local headroom, and the return of shared headroom after the group is released. The previously refused job must then complete on its first attempt. At PR head `3cd136ad` and tested merge `e1fa7f1d`, the case passed in the 62-case Linux suite and the 154-case macOS suite. [Hosted Linux suite](https://github.com/TryUniCAD/Kit/actions/runs/43781577583/job/133019771709), [hosted macOS suite](https://github.com/TryUniCAD/Kit/actions/runs/43781577583/job/133019772047)

See [supervisor commands](../../../Reference/Research/ResearchSupervisor.md#commands) and [pool capacity](../../../Reference/Research/ParallelSessions.md#capacity-how-many-sessions-run-at-the-same-time).
