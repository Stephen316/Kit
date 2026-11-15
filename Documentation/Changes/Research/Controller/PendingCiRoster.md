# Freeze a pending CI batch roster

Select the exact Git commit available in this checkout and the current controller jobs waiting for CI.

```sh
python3 re/automation/CiBatch.py --store /path/to/ResearchStore \
  --batch-revision FULL_COMMIT_SHA --job candidate:first --job candidate:next
```

The command reads one A03 snapshot. Each selected job must still be parked after a settled `waiting_ci` attempt. The command verifies the immutable definition, fingerprint, snapshot, result, receipt and attempt history. It checks the declared `ci` input against the current named binding and artifact. Use `--ci-role` when the jobs declare that binding under a different input role.

The output identifies the batch revision, canonical job order and exact pending evidence. The `payload_sha256` hashes the canonical report fields excluding that digest field. Save the output as the proposed batch roster. A later controller rebind or new attempt changes eligibility and requires a fresh check. This command reads the controller and Git store. Stage 11 research verification and a terminal hosted CI result have their own evidence.

The hosted process fixture uses real A03 `waiting_ci` outcomes, verifies deterministic output and ledger bytes, and checks refusal after a member's binding or retained receipt changes. Hosted verification of this change is pending. [Batched remote verification plan](../../../Reference/Research/AutomationPlan.md#batched-remote-verification)
