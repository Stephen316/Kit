# Admit one verified Fusion archive retry

Add `--admit-archived-retry` to the continuing macOS owner that already
opts into [replacement control](FusionArchivedControl.md). The owner
compares the still-parked first attempt, its settled receipt and result,
the commissioned reservation, and the exact replacement control and
process under the dispatch lock and one A03 write transaction.

The control must still be fresh on both wall and monotonic clocks. The
exact replacement must still hold the application host and the original
retry delay must allow admission within that validity window. The
transaction retains the control request, reservation, result, process and
startup bytes by digest, journals the admission, and makes only the
reserved Phase A eligible for its second attempt. Phase B still waits for
accepted Phase A evidence.

The A03 attempt cap for that verified definition and generation is two,
including on retry settlement or lease expiration. The original job
definition and budget for other jobs stay compatible. A later owner
process can observe the durable event. A missing response, changed
generation or spent budget leaves this archive ineligible for another
automatic admission. The worker still runs its normal pre-dispatch probe.

The hosted case uses a disposable AppKit process and an Autodesk API
stand-in to exercise replacement custody and control. It then uses the
actual A03 commands to select the exact second lease ahead of an older
rival and check failure after retry settlement and lease expiration. It
also checks the durable evidence and generation invalidation. Hosted
verification and signed-in Fusion retry acceptance remain pending.
