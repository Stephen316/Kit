# Supervisor recovery owner epoch

The A03 supervisor adapter now fences its controller subprocesses with a random
owner epoch. This closes a recovery race in which an orphaned claim invocation
could publish a claim after a restarted supervisor had scanned for orphan files.

After acquiring both existing OS locks, the supervisor calls `BeginOwner` before
recovery. A03 commits a new 64-hex-character owner epoch. Every subsequent adapter
invocation carries that exact epoch through the controller's global `--owner`
argument. The raw value stays out of runner records; the controller stores its
SHA-256 digest in an optional version 1 `supervisor_owner` table.

The controller verifies the epoch inside the same `BEGIN IMMEDIATE` transaction
that performs the operation, publishes claim files and commits job state.
[SQLite permits one write transaction at a time](https://www.sqlite.org/lang_transaction.html).
An older invocation therefore either commits before epoch rotation, making its
published claims visible to recovery, or begins afterward and fails before
claim/publication work. A stale owner returns exit status 5. Stale job leases
retain their separate exit status 3.

## Adapter compatibility

`RecoveryFenceVersion = 1` advertises the optional recovery capability. A supporting
adapter provides `BeginOwner()` and returns exactly
`{"recovery_fence_version": 1}` after installing its fence. Invalid versions or a
missing method fail before recovery. Required legacy adapter operations and the
single-job protocol remain unchanged.

Standalone controller calls without `--owner` remain supported. Custom adapters
without this capability retain their existing recovery behavior. Older deployed
supervisors that do not send an epoch remain unfenced, even if the optional table
exists. Protection requires the participating supervisor, adapter and controller
versions together; this change does not claim protection for legacy invocations.

`rotate-owner --new-owner <epoch>` is the internal A03 operation used while the
supervisor holds its OS locks. Workers do not rotate epochs or receive them.

## Verification

`tests/Research/Owners` adds real process interruption cases for solo and grouped
claims. A fixture wrapper holds a controller invocation before it starts its
transaction. The test verifies the actual supervisor/gated-child parent chain and
lock ownership, kills the supervisor, starts a replacement, observes a committed
new epoch, then releases the old invocation. The old invocation must return exit
status 5 without publishing its claim; current-owner jobs must complete with one
attempt each.

Windows coverage checks the actual interpreter PID and its parent chain through
the supported `Win32_Process` provider, allowing the CPython venv redirector.
It terminates the recorded supervisor PID rather than assuming `Popen.pid` is the
interpreter. Fixture contexts release gates and clean their owned subprocesses on
failure. Separate process cases reject invalid capability declarations.

AST, steering, Mypy, Pyright, Black and whitespace checks passed. Local tests were
not run. Remote Linux, macOS and Windows execution remains required. This recovery
mechanism establishes no native CAD qualification or merge-queue acceptance.

See [the orphan-controller gotcha](../../../Gotchas/Research/Workers/OrphanControllerClaims.md).
