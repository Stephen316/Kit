# Deterministic CLI compatibility with an external research checkout

## Behavior and scope

The CLI compatibility suite lives in `tests/CliResearch/`. It exercises the
installed CLI against a separate PR94 checkout rather than including PR94's
research implementation or SDK changes in the CLI branch.

Set the test-only `KIT_RESEARCH_CHECKOUT` environment variable to the absolute
path of the immutable research checkout provisioned by CI. Missing or relative
paths fail the suite; no fallback checkout or skipped compatibility result is
accepted. The installed CLI executes as `python -I -m convert` from a temporary
working directory. Direct reference readers execute by absolute path from the
selected checkout. Neither the suite nor its parent process imports that
checkout's SDK or changes `PYTHONPATH` to select it. The research scripts select
their own SDK in their fresh process, as required by their existing contract.

Remote invocation after installation and the pinned checkout step:

```sh
KIT_RESEARCH_CHECKOUT=/absolute/pinned/research/checkout uv run --no-sync --python 3.14 python -m pytest tests/CliResearch -q
```

The same checkout environment must be available to complete-suite CI jobs that
execute these cases. The pin and CI configuration belong to the CLI PR; the
tests verify receipt identity against that checkout's actual Git revision and
SDK source digest.
The compatibility pin is PR #94 revision `b86f30c7e41abdc3812ada795a193377f6ddd220`,
including the blind-boss correction, direct-write safeguards, bounded session logs,
and supervisor memory/resource headroom controls after CLI implementation was separated.
The dedicated job is registered in the CI allowlist, and merge-group shards select the same checkout when they execute this suite.
The Windows compatibility job runs pinned reader, rejection, and controller cases with the same checkout.
Windows launches wait for the child and forward its exit status; Linux and macOS retain process replacement.
The supervisor's platform refusal is checked through the actual CLI.
New action references retain the required version annotations, and shard selection uses the runner's standard `grep` command.
Root `AGENTS.md` documents installation, pinned decoding, receipts, and existing controller/supervisor commands for developers and agents.

## Process coverage and limits

SOLIDWORKS and Fusion cases compare all generated artifact bytes with direct
reader runs, including receipts, summaries, unqualified research metadata, SDK
identity, and neutral-document hashes. They exercise existing-output refusal,
all four corpus pin fields, batch preflight refusal, strict Fusion status 3,
root-option forwarding guards, parser status 2, and controller help.

A durable controller case binds an input, submits and claims a job, changes the
bound input, and verifies stale-lease status 3 and requeueing. The supervisor
case configures an absolute fixture worker from the research checkout, observes
actual dispatch, rejects a second supervisor with status 4, pauses and stops the
active session, resumes its pool, and verifies successful result publication.
The fixture is a test process; this suite neither invokes external models or CAD
applications nor claims a production decoding agent or native acceptance result.

## Verification

No local tests, reader runs, or test collection were executed. Pinned formatting,
type analysis, repository steering, path policy, and diff checks cover these
files. Actual subprocess execution must pass in remote CI on the accepted CLI
head with the explicitly pinned research checkout. Target-application acceptance
remains a separate requirement.
See [Windows exit-status handling](../../Gotchas/Packaging/WindowsResearchExitStatus.md).
JSON fixture reads use raw bytes to avoid [locale-dependent decoding](../../Gotchas/Ci/Commands/ResearchFixtureEncoding.md).
