# Run deterministic research with Kit

## Purpose

Run PR #94's pinned readers, corpus, durable controller, and configured supervisor through the installed `kit` command.
The CLI delegates to existing implementations and preserves their evidence contracts.
Users do not write Python imports or scripts.

## Before you start

Install a CLI revision from its source checkout with `uv tool install .`.
Use `uv tool install --python 3.14 .` when Fusion research is required.
The launcher uses the interpreter running `kit` and does not silently select another environment.
The equivalent module command is `python -m KitCli research`.
`python -m convert research` reports an error directing callers to these developer entry points.

Select a trusted checkout containing PR #94 and the corpus's pinned Git objects.
`--root` authorizes execution of that checkout's research code and SDK.
The wheel contains the SDK and CLI, not research fixtures or the `re/` workspace.
The supervisor requires Linux or macOS.
On Windows, reader, corpus, and controller commands wait for completion and return the tool's exit status.

The examples use `/path/to/KitPr94` for the trusted research checkout.
Replace it with its absolute path; the installed CLI checkout can be different.
Replace example output paths with unused directories that you own.
Preserve the original CAD files.

## Decode committed inputs

Decode a pinned SOLIDWORKS part:

```sh
kit research --root /path/to/KitPr94 solidworks --asset re/solidworks/examples/.SLDPRT/example.SLDPRT --output /tmp/KitPinnedPart
```

Inspect `receipt.json` before using `document.json`.
Retain both files for subsequent research.
The reader selects committed Git bytes and verifies path, blob, size, SHA-256, and prefix.
The document remains unchanged SDK `CadDocument` serialization.
Research documents carry `kit.research_read_status: unqualified` in their existing metadata field.
The CLI refuses conversion of those marked documents, including marked nested components, before staging output.
Keep the marker and receipt; the CLI does not promote research results into qualified conversion inputs.
The separate receipt binds source, SDK, tools, options, hashes, and unresolved evidence.

For Fusion, use Python 3.14 and select one or more committed assets:

```sh
kit research --root /path/to/KitPr94 fusion --asset re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d --output /tmp/KitPinnedFusion
```

Repeat `--asset` for up to 1000 distinct inputs.
Fusion publishes `summary.json` and separate document/receipt directories for decoded assets.
Exit status `3` means a published run contains rejected or reader-error outcomes.
Inspect every outcome before interpreting the batch.

Use `--manifest PATH` for another supported manifest.
SOLIDWORKS also accepts `--configuration NAME`.
Fusion `--allow-partial` means strict-first decoding with explicit fallback, unlike inspection's forced `--partial` reader mode.
Set `--root` once before the tool name; forwarded root overrides and their abbreviations are rejected.
Use `kit research --root /path/to/KitPr94 fusion --help` for the authoritative reader help.

Expected result: the existing reader publishes its normal artifacts or reports its existing failure.
Successful receipts do not establish portable completeness or native conversion acceptance.

## Manage durable research jobs

The corpus and controller retain their existing commands:

```sh
kit research --root /path/to/KitPr94 corpus check --manifest /path/to/KitPr94/re/automation/Corpus.json
kit research --root /path/to/KitPr94 controller --store /tmp/KitResearchState init --max-running 4
kit research --root /path/to/KitPr94 controller --store /tmp/KitResearchState status
```

Use `controller --help` for evidence binding, batch submission, claims, lease renewal, and result submission.
The CLI preserves stale-lease status `3` and the controller's integrity checks.

## Run configured sessions

Prepare an actual runner registry and `Supervisor.json` with the [supervisor guide](https://github.com/Stephen316/Kit/blob/b86f30c7e41abdc3812ada795a193377f6ddd220/Documentation/Reference/Research/ResearchSupervisor.md).
Use only trusted configuration and runner programs.

```sh
kit research --root /path/to/KitPr94 supervisor --config Supervisor.json submit Batch.json
kit research --root /path/to/KitPr94 supervisor --config Supervisor.json run --idle-seconds 30
kit research --root /path/to/KitPr94 supervisor --config Supervisor.json status
kit research --root /path/to/KitPr94 supervisor --config Supervisor.json pause decode --reason "operator hold"
kit research --root /path/to/KitPr94 supervisor --config Supervisor.json resume decode
```

The supervisor owns pools, claims, leases, retries, restart fencing, and configured worker dispatch.
On Linux and macOS the CLI starts a separate research session and owns signal handling before spawning it.
Interrupt, termination, hangup, quit, and user signals are forwarded; terminal suspension stops both launcher and child, and continuation resumes the child.
Startup signals wait for the child reference, and continuation cancels a queued suspension.
It waits for cleanup, preserves output and exit statuses, and terminates with the child's signal when that child is killed.
An uncatchable launcher kill cannot be forwarded; use the existing research lease and recovery controls after forced termination.
Supervisor contention retains status `4`.

No production decode runner or model-provider registry is supplied by this bridge.
Models remain disabled by default.
Optional Codex/Claude runners, escalation, budgets, and private-data controls remain A10 work under the plan's authorization rules.
Application workers remain separate isolated research oracles.
See [session output lifetime](../Gotchas/Research/SupervisorSessionOutputLifetime.md) before implementing a persistent decode runner.

## Keep the interfaces distinct

| Command                                       | Contract                                                   |
| --------------------------------------------- | ---------------------------------------------------------- |
| `kit convert SOURCE DESTINATION`              | User conversion through the SDK and its output policy      |
| `kit decode SOURCE`                           | Working-file inspection with a `kit.decode` report         |
| `kit research --root CHECKOUT solidworks ...` | Pinned input, unchanged neutral document, separate receipt |
| `kit research --root CHECKOUT fusion ...`     | Pinned batch, per-asset receipts, run summary              |
| `kit research --root CHECKOUT supervisor ...` | Existing configured runner sessions and controller state   |

The research checkout can differ from the installed CLI checkout.
The selected script starts in a fresh interpreter and explicitly loads its own SDK source.
The CLI forwards reader output and exit codes without reconstructing fingerprints or receipts.
It executes no shell and imports no research modules into production conversion.
The packaged `KitCli` developer composition lives in `Cli/`, separately from the two SDK packages in `src/`.
Conversion and inspection do not import its process launcher dependencies.

## If the command fails

| Symptom                           | Action and stop condition                                          |
| --------------------------------- | ------------------------------------------------------------------ |
| Missing research script           | Select the intended trusted PR #94 checkout                        |
| Missing pinned Git object         | Fetch the manifest's committed revision before retrying            |
| Hash or prefix mismatch           | Restore or review the intended pin; do not relax checks            |
| Existing output directory         | Choose an unused path; no overwrite bypass is exposed              |
| Fusion requires Python 3.14       | Install or run the CLI with that interpreter                       |
| Supervisor unavailable on Windows | Use Linux or macOS for orchestration                               |
| Runner unavailable                | Configure an implemented runner or retain the blocked prerequisite |

Tests execute only in remote CI.
See [the change record](../Changes/Research/DeterministicResearchCli.md) for compatibility coverage and limits.

## Related information

- [General CLI](CommandLine.md)
- [Research plan](https://github.com/Stephen316/Kit/blob/b86f30c7e41abdc3812ada795a193377f6ddd220/Documentation/Reference/Research/AutomationPlan.md)
- [Step register](https://github.com/Stephen316/Kit/blob/b86f30c7e41abdc3812ada795a193377f6ddd220/Documentation/Reference/Research/AutomationSteps.md)
- [SOLIDWORKS reader](https://github.com/Stephen316/Kit/blob/b86f30c7e41abdc3812ada795a193377f6ddd220/Documentation/Reference/Research/SolidworksResearchReader.md)
- [Fusion reader](https://github.com/Stephen316/Kit/blob/b86f30c7e41abdc3812ada795a193377f6ddd220/Documentation/Reference/Research/FusionResearchReader.md)
