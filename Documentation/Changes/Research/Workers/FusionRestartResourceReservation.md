# Reserve an installation through the Fusion restart

For a pinned macOS installation with automatic quit and supervised
acknowledgement configured, pass `--owner-lifecycle --receipt <private-json>`
to `QueueFusionPhases.py` before either job has been claimed. Use the exact
reviewed controller and supervisor checkout and the capacity-one
`application:<installation>` resource. The private receipt format and existing
receipt recovery command are unchanged.

A03 records the reservation in the same transaction as the registered Phase A
settlement. Only the exact registered Phase B can use that resource after the
owner verifies the drained acknowledgement and binds the retained restart
intent. The rule is shared by ordinary and group claims and by the eligibility
check that gives requested grids precedence over standard grids. A03 keeps
physical capacity and timeout holds under their existing accounting.

The owner releases the reservation after it saves and verifies final Phase B
evidence. Recovery compares the exact accepted attempts and receipt hashes
again before releasing it. A changed acceptance or an unresolved receipt
keeps the installation reserved. Existing unregistered and manual queue
submissions use their original admission rules.

The hosted cases use the real A03 claim, settlement, acknowledgement recovery,
and grid scheduler. They interrupt the supervisor after Phase A settlement,
make older contenders runnable, preserve an unrelated timeout hold, and use
disposable lifecycle providers for the accepted-exit and Phase B recovery
boundaries. Both contention cases passed in the 161-case macOS suite at
PR head `14f4a1f2` and tested merge `1198983e`. A signed-in Fusion run
remains pending. [Hosted macOS evidence](https://github.com/TryUniCAD/Kit/actions/runs/43788486237/job/133041436716)

[Owner program](FusionLifecycleOwner.md), [Grid admission and restart fences](../../../Gotchas/Research/Workers/FusionGridPrecedenceRequiresAdmission.md)
