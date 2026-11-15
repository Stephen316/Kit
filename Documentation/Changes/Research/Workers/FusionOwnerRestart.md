# Fusion owner restart intent

After A03 accepts Phase A and the [application acknowledgement](ApplicationAcceptance.md) has released its spool, the installation owner can register the exact retained handoff.

```sh
python re/automation/ApplicationWorkers/FusionOwnerRestart.py \
  --installation /private/fusion/Installation.json \
  --store /private/fusion/Store \
  --queue-receipt /private/fusion/QueueReceipt.json
```

Use the [phase queue receipt](FusionPhaseQueue.md) from the original submission. The owner command checks the current accepted attempt and its artifacts through a read-only A03 snapshot, verifies the installed source pins, and requires Phase A's accepted host identity to match both the retained fence and the live process. Pending acknowledgement or a retained Phase A spool keeps the gate closed.

The command writes one immutable `restart-intent-<handoff-id>.json` inside the private endpoint. Repeating registration requires those exact bytes. Add `--check` to verify the existing intent against current evidence without changing the endpoint or the A03 store. The [macOS peer verifier](FusionRestartPeer.md) additionally binds the handoff to the live OS process and a pinned application bundle.

This checkpoint records no application quit, launch, or native readiness. The [verified startup fence](FusionRestartStartup.md) and normal Phase B fresh-process checks still control admission. Licensed Fusion and an authorized lifecycle provider are required for an unattended restart.
