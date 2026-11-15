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

The [two-body through-all plan](../FusionReadback/FusionScopeControl.md) uses the same queue command and signed-in add-in. Its receipt identifies the fixed automatic, explicit-A and explicit-A+B cases. Phase B stages Phase A's accepted A03 result and its exact report, receipt and three archives. The native worker checks the accepted artifacts before it runs the next phase. The [read-only audit](FusionPhaseAudit.md) checks the linked reports and process identities under their scope receipt.

Save that receipt to [check both phases and their accepted output evidence](FusionPhaseAudit.md) from the private controller store.

Native execution uses the signed-in macOS Fusion installation and its existing `KitCaptureRunner` endpoint. The add-in supplies a fresh main-thread control. Phase A hands off to the host owner for normal exit and restart of the same Fusion build. After A03 acknowledges Phase A, Phase B can hold its normal claim and counted resource slot while the exact restart fence is present. The wait fits within the existing dispatch deadline and leaves the application spool, acknowledgement state and fence untouched. Once the new add-in clears that fence and the original process has exited, Phase B runs the existing live readiness control and retains the capture-specific restart checks.

If the exact fence stays in place until the deadline, a different fence is present or the old process is still alive after the fence disappears, Phase B parks under the usual resource rules. Malformed accepted handoff evidence rejects the attempt. A phase that parks while the host is unavailable requires the installation's existing resource reactivation. The queue command leaves that resource's availability under the host owner's control. [Local dispatch and host setup](LocalApplicationDispatch.md) [Fresh-process procedure](../FusionReadback/FusionFreshProcessEvidence.md)

The hosted process case checks exact pairing, repeat submission, preserved resource availability and rejection of an altered control pin with an absent endpoint. Hosted case execution is pending. The licensed two-process Fusion run still requires a provisioned macOS host.

The restart wait has hosted process cases for a replacement host, deadline, foreign fence, still-running original process and malformed accepted handoff. The fixture uses shared queue ownership and invokes no CAD APIs.

When a dispatched probe or capture request times out, its parked controller result retains the queue job ID, request SHA-256, operation, source revision and plan SHA-256. The request hash binds the exact private spool record. The worker keeps the existing cancellation and quarantine rules, and the controller continues to park the resource. Recovery still depends on the installation owner.
