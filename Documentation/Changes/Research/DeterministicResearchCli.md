# A08d — Deterministic research CLI compatibility

## Behavior

PR #94 incorporates PR #119's installed conversion and inspection command.
`kit research --root CHECKOUT TOOL ...` delegates to the implemented pinned readers, corpus, controller, and supervisor.
The tools are `solidworks`, `fusion`, `corpus`, `controller`, and `supervisor`.
Follow [the CLI procedure](../../Tasks/ResearchCommandLine.md) for installation, commands, and recovery.

The selected trusted checkout supplies the executed SDK and research code.
The wheel retains its SDK-only package scope.
A fixed script allowlist and process replacement preserve output, native statuses, and signals without a shell or research imports.
Pinned document JSON, separate receipts, fingerprints, and Fusion summaries remain authoritative.
The launcher does not rebuild their contracts.
Stale leases and incomplete Fusion batches retain status `3`; supervisor contention retains `4`.

## Limits

Ordinary `kit decode` remains working-file inspection, separate from deterministic research artifacts.
Existing reader qualification limits and native acceptance requirements remain in force.
Fusion research requires Python 3.14; the supervisor requires Linux or macOS.
No production scheduled decode runner, persistent worker-output ingestion, model provider, or optional A10 implementation is introduced.
Models remain disabled by default, and missing workers remain explicit prerequisites.
A08d does not close A05, A08a, A10, or semantic qualification steps.

## Verification

Read-only reader and supervisor audits checked command contracts, ownership, exit statuses, SDK identity, and session output lifetime.
Remote process cases compare direct and CLI document/receipt bytes and full Fusion artifact sets.
They cover pin tampering, overwrite refusal, invalid checkout, root abbreviations, help, stale leases, pool pause/resume, configured worker dispatch, and lock contention.
Existing reader/controller/supervisor suites remain enabled in the registered workflow-quality job.
New CLI compatibility cases execute there on Python 3.14.
No local tests, decoding, model calls, or CAD experiments were run.
Exact-head remote results and configured review are recorded in PR #94 comments and the step register.

See [checkout SDK identity](../../Gotchas/Research/ResearchCheckoutSdkIdentity.md) and [session output lifetime](../../Gotchas/Research/SupervisorSessionOutputLifetime.md).
