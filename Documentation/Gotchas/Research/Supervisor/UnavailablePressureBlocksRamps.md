# Unavailable pressure data blocks upward ramps

## Expectation

Basic CPU and available-memory measurements can appear sufficient to qualify a healthy adaptive increase.

## Actual behavior

The plan also requires a one-minute load guard and a Linux memory PSI guard.
A Linux kernel can lack the `/proc/pressure/memory` interface.
The current Windows implementation supplies no load-average equivalent.
Those observations remain unavailable rather than becoming fabricated zeros.
Likewise, an exit signal alone does not establish an operating-system OOM cause.

## Workaround

Keep the measured admission ceiling and conservative startup limit.
Report the unavailable guard through `upward_blocked_reason` and wait for valid measurements before increasing capacity.
Use the real host observations when interpreting remote branch coverage.
Do not claim the upward branch merely because its no-early-increase scenario passed.
Do not relabel `SIGKILL` as OOM evidence.

See [the Linux PSI interface](https://docs.kernel.org/accounting/psi.html) and [the adaptive change entry](../../../Changes/Research/Supervisor/AdaptivePoolLimits.md).
