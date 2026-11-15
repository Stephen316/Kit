# Fusion phase can become ready before the application restarts

The supervisor can accept and acknowledge Phase A while the original Fusion process is still alive. At that point the controller can dispatch Phase B and the installation can still carry the restart fence. Treating every fence as immediately unavailable parks the application resource during a normal handoff.

Phase B waits inside its original deadline for the exact restart fence in the accepted Phase A receipt. The installation remains reserved for this claim, and other application resources retain their own capacity. When the fence clears, the worker verifies the prior process exited before probing the new host. A different fence, acknowledgement still pending, or an unverified restart produces a waiting-application result. [Queue handoff](../../../Changes/Research/Workers/FusionPhaseQueue.md)

Phase A checks the application queue before reading the plan, preserving the waiting-application result for an absent endpoint. The first hosted restart run passed both Phase B cases but exposed that check-order regression in the Phase A parking case. [macOS worker run](https://github.com/TryUniCAD/Kit/actions/runs/43721778227/job/132835216139)

The replacement can acquire the queue lock before the add-in verifies its bootstrap. Releasing the fence at lock acquisition lets the next claim publish a probe even if startup fails. The native queue now retains that restart fence until the verified startup reaches its event loop with the installed source pins. [Replacement startup evidence](../../../Changes/Research/Workers/FusionRestartStartup.md)
