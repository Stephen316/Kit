# Check the Fusion endpoint before Phase A inputs

The worker parks when the configured owner endpoint is unavailable. The [macOS worker at `2eb009ee`](https://github.com/TryUniCAD/Kit/actions/runs/43759069926/job/132949593028) rejected the Phase A job on its missing plan input first, so the supervisor could not record the application wait.

After checking the pinned installation, acquire the Phase A queue client before opening the plan. Phase B still checks the accepted Phase A result and the restart fence before acquiring a new client.
