# Queue both Fusion fresh-process phases

After preparing a pinned Fusion plan, run the queue command with the existing supervisor configuration and the installation's counted resource label.

```sh
python3 re/automation/ApplicationWorkers/QueueFusionPhases.py \
  --config /absolute/path/Supervisor.json \
  --plan /absolute/path/paired-run-01/plan.json \
  --resource application:fusion:local
```

The command uses the built-in A03 store and the registered `capture.fusion` runner by default. Pass `--kind` for a different configured runner label. It verifies the plan through the same trusted-revision check used by the native counterpart. The command binds the exact plan and submits both phases in one controller transaction. Phase B receives Phase A's accepted result, receipt, measurements and pinned per-recipe archives through dependency selectors.

The receipt prints the installation, exact revision, plan digest and phase job IDs. Repeat the command to recover the same IDs without creating a second pair. Set `--run` to a new label to schedule a separate capture from the same plan. An existing job with a conflicting definition or a changed content-addressed binding causes the transaction to fail.

Native execution uses the signed-in macOS Fusion installation and its existing `KitCaptureRunner` endpoint. The add-in supplies a fresh main-thread control. Phase A hands off to the host owner for normal exit and restart of the same Fusion build. Phase B verifies the new process and the old process exit. A phase that parks while the host is unavailable requires the installation's existing resource reactivation. The queue command leaves that resource's availability under the host owner's control. [Local dispatch and host setup](LocalApplicationDispatch.md) [Fresh-process procedure](../FusionFreshProcessEvidence.md)

The hosted process case checks exact pairing, repeat submission, preserved resource availability and rejection of an altered control pin with an absent endpoint. Hosted case execution is pending. The licensed two-process Fusion run still requires a provisioned macOS host.
